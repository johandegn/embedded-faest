#!/usr/bin/env python3
# This script uses the prepare_nist.py script to export the
# specified faest variants to the pqm4 project.

import os
import subprocess
import argparse
import shutil

BASE_VARIANTS = ['128', '192', '256', 'em128', 'em192', 'em256']
FAST_VARIANTS = [f'{v}f' for v in BASE_VARIANTS]
SLOW_VARIANTS = [f'{v}s' for v in BASE_VARIANTS]
VALID_VARIANTS = FAST_VARIANTS + SLOW_VARIANTS

FILEPATH = os.path.dirname(os.path.realpath(__file__))
TEST_BUILD_PATH = f'{FILEPATH}/test/build'
TEST_RESULT_PATH = f'{FILEPATH}/test/results'
TEST_FILE_PATH = f'{FILEPATH}/test/files'

TEST_FILE_NAME = 'faest-test.c'


# Append 'faest_' and insert '_' between 'em' and '128f'
def transform_variants(variants):
    new = []
    for v in variants:
        name = v
        if v.startswith('em'):
            name = f'em_{v[2:]}'
        name = f'faest_{name}'
        new.append(name)
    return new


def parse_args():
    parser = argparse.ArgumentParser(description='FAEST memory profiler.')

    parser.add_argument('-t', '--threads', type=int, default=1,
                        help='Thread count. Set to 0 for max utilization (default: 1)')
    parser.add_argument('variants', nargs='*',
                        help='List of variants. If empty, all is run')
    parser.add_argument('-s', '--slow', action='store_true', default=False,
                        help='Include slow if variants is empty (default: False)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        default=False, help='Be verbose')
    parser.add_argument('--no-openssl', action='store_true',
                        default=False, help='Disables optimization for OpenSSL')
    parser.add_argument('--no-massif', action='store_true',
                        default=False, help='Disables massif memory profiler')

    args = parser.parse_args()

    # Check variants
    for v in args.variants:
        if v not in VALID_VARIANTS:
            raise argparse.ArgumentTypeError(
                f'{v} is not a valid variant. Only {VALID_VARIANTS} may be used')

    if not args.variants:
        variants = VALID_VARIANTS if args.slow else FAST_VARIANTS
    else:
        variants = args.variants
    variants = transform_variants(variants)

    threads = args.threads
    if threads <= 0:
        threads = os.cpu_count()
    threads = min(threads, len(variants))

    return {'threads': threads, 'variants': variants, 'verbose': args.verbose, 'no-openssl': args.no_openssl, 'no-massif': args.no_massif}


# Compiles the reference implementation
def compile_faest(verbose=False):
    if verbose:
        process = subprocess.Popen('ninja', cwd='faest/build/', text=True)
    else:
        process = subprocess.Popen(
            'ninja', cwd=f'{FILEPATH}/faest/build/', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    code = process.wait()
    if code != 0:
        exit(1)


def ensure_folder(path):
    os.makedirs(path, exist_ok=True)


def copy(src, dst):
    if dst[-1] == '/':
        dst = dst[:-1]
    path = '/'.join(dst.split('/')[:-1])
    ensure_folder(path)
    shutil.copyfile(src, dst)


# Copy files needed for given variants to build folders
def copy_files(variant):
    files = [('faest/', 'faest_defines.h'),
             ('faest/build/', f'{variant}.h'),
             (f'faest/build/{variant}/', 'api.h'),
             (f'faest/build/{variant}/', 'crypto_sign.h'),
             (f'faest/build/{variant}/', 'crypto_sign.c')]
    for path, file in files:
        copy(f'{FILEPATH}/{path}{file}', f'{TEST_BUILD_PATH}/{variant}/{file}')


def compile(variant):
    # TODO: take TEST_FILE_NAME as argument to allow multiple test files
    copy(f'{TEST_FILE_PATH}/{TEST_FILE_NAME}', f'{TEST_BUILD_PATH}/{variant}/{TEST_FILE_NAME}')

    compiler = 'gcc'
    link_path = f'{FILEPATH}/faest/build'

    cmd = [compiler, f'-L{link_path}', '-lfaest', '-o',
           'faest-test', 'crypto_sign.c', TEST_FILE_NAME]
    cwd = f'{TEST_BUILD_PATH}/{variant}'
    process = subprocess.Popen(
        cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    code = process.wait()
    if code != 0:  # TODO
        exit(1)


def start_process(variant, no_massif):
    cmd = []

    if not no_massif:
        # Run with memory check
        ensure_folder(TEST_RESULT_PATH)
        cmd += ['valgrind', '--tool=massif', '--stacks=yes',
                f'--massif-out-file={TEST_RESULT_PATH}/massif_{variant}']

    cmd += [f'{TEST_BUILD_PATH}/{variant}/faest-test']

    env = os.environ.copy()
    # Linux dynamic lib path
    env['LD_LIBRARY_PATH'] = f'{FILEPATH}/faest/build'
    # MacOS dynamic lib path
    env['DYLD_LIBRARY_PATH'] = f'{FILEPATH}/faest/build'

    return subprocess.Popen(cmd, cwd=FILEPATH, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, text=True)


def run_all(args):
    remaining = args['variants'].copy()
    threads = []
    done = []

    # Keep specified amount of threads bussy
    while len(remaining) > 0:
        if args['threads'] > len(threads):
            variant = remaining.pop()
            threads.append(
                (variant, start_process(variant, args['no-massif'])))

        # Remove if done
        done += [(v, p.returncode) for v, p in threads if not p.poll() == None]
        threads = [(v, p) for v, p in threads if p.poll() == None]
    # Wait for the rest to finish
    for v, p in threads:
        code = p.wait()
        done.append((v, code))

    # Check return codes
    success = True
    for v, c in done:
        if c != 0:
            print(f'{v} returned \'{c}\'')
            success = False

    if not success:
        exit(1)


def compile_all(args):
    for v in args['variants']:
        copy_files(v)
    for v in args['variants']:
        compile(v)


def disable_openssl():
    os.rename(f'{FILEPATH}/faest/aes.c', f'{FILEPATH}/faest/aes_old.c')
    shutil.copyfile(f'{TEST_FILE_PATH}/aes_no_openssl.c',
                    f'{FILEPATH}/faest/aes.c')


def restore_openssl():
    os.replace(f'{FILEPATH}/faest/aes_old.c', f'{FILEPATH}/faest/aes.c')


# ninja does not seem to always detect changes, use this to force rebuild (fx going from openssl to without)
def clean_faest():
    subprocess.run(['ninja -t clean'], cwd=f'{FILEPATH}/faest/build/',
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)


if __name__ == '__main__':
    args = parse_args()
    # TODO Remove Keccak optimizations (if any?)
    # TODO Remove AVX optimizations (Why are they here? compiler complained about them..)
    if args['no-openssl']:
        print('Disabling OpenSSL')
        disable_openssl()

    print('Rebuilding FAEST')
    clean_faest()  # TODO do this until ninja is behaves
    compile_faest(args['verbose'])

    if args['no-openssl']:
        print('Restoring OpenSSL')
        restore_openssl()

    print('Compiling variants')
    compile_all(args)

    print(f'Running variants ({args["threads"]} thread(s))')
    run_all(args)
