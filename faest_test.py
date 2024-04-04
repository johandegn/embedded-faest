#!/usr/bin/env python3
# This script uses to test and benchmark specified faest variants

import os
import subprocess
import argparse
import shutil
import time

from parse_massif import parse_and_write

COMPILER = 'gcc'

BASE_VARIANTS = ['128', '192', '256', 'em128', 'em192', 'em256']
FAST_VARIANTS = [f'{v}f' for v in BASE_VARIANTS]
SLOW_VARIANTS = [f'{v}s' for v in BASE_VARIANTS]
VALID_VARIANTS = FAST_VARIANTS + SLOW_VARIANTS

FILEPATH = os.path.dirname(os.path.realpath(__file__))
TEST_BUILD_PATH = f'{FILEPATH}/test/build'
TEST_RESULT_PATH = f'{FILEPATH}/test/results'
TEST_RESULT_MASSIF_PATH = f'{TEST_RESULT_PATH}/massif'
TEST_RESULT_CALLGRIND_PATH = f'{TEST_RESULT_PATH}/callgrind'
TEST_FILE_PATH = f'{FILEPATH}/test/files'

# TEST_FILE_NAME = 'faest_test.c'
TEST_KEYGEN_FILE_NAME = 'faest_test_keygen.c'
TEST_SIGN_FILE_NAME = 'faest_test_sign.c'
TEST_VERIFY_FILE_NAME = 'faest_test_verify.c'

TEST_LIST = (('keygen', TEST_KEYGEN_FILE_NAME),
             ('sign', TEST_SIGN_FILE_NAME), ('verify', TEST_VERIFY_FILE_NAME))
TEST_NAMES = list(name for (name, _) in TEST_LIST)

TOOL_NAMES = ['massif', 'callgrind']


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
    parser.add_argument('--tests', nargs='+',
                        help='List of tests. If not specified, all is run. (Tests might depend on each other)')
    parser.add_argument('-s', '--slow', action='store_true', default=False,
                        help='Include slow variants if variants argument is empty (default: False)')
    parser.add_argument('--tool', default=None,
                        help='Select valgrind tool for profiling (massif or callgrind)')
    parser.add_argument('--no-openssl', action='store_true',
                        default=False, help='Disables OpenSSL optimization')
    parser.add_argument('--no-forced-rebuild', action='store_true',
                        default=False, help='Disables forced ninja rebuild of FAEST')
    parser.add_argument('-v', '--verbose', action='store_true',
                        default=False, help='Be verbose')

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

    # Check tests
    if args.tests:
        for t in args.tests:
            if t not in TEST_NAMES:
                raise argparse.ArgumentTypeError(
                    f'{t} is not a valid test. Only {TEST_NAMES} may be used')

    if not args.tests:
        tests = TEST_NAMES
    else:
        tests = args.tests

    # Check tool
    if args.tool and args.tool not in TOOL_NAMES:
        raise argparse.ArgumentTypeError(
            f'{t} is not a valid tool. Only {TOOL_NAMES} may be used')

    # Threads
    threads = args.threads
    if threads <= 0:
        threads = os.cpu_count()
    threads = min(threads, len(variants))

    return {'threads': threads,
            'variants': variants,
            'tests': tests,
            'tool': args.tool,
            'verbose': args.verbose,
            'no-openssl': args.no_openssl,
            'no-forced-rebuild': args.no_forced_rebuild}


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


def ensure_result_folder(args):
    if args['tool'] == 'massif':
        ensure_folder(TEST_RESULT_MASSIF_PATH)
    if args['tool'] == 'callgrind':
        ensure_folder(TEST_RESULT_CALLGRIND_PATH)


def copy(src, dst):
    if dst[-1] == '/':
        dst = dst[:-1]
    path = '/'.join(dst.split('/')[:-1])
    ensure_folder(path)
    shutil.copyfile(src, dst)


# Copy files needed for given variants to build folders
def copy_files(variant):
    files = [('faest/', 'faest_defines.h'),
             (f'test/files/', 'faest_test.h'),
             ('faest/build/', f'{variant}.h'),
             (f'faest/build/{variant}/', 'api.h'),
             (f'faest/build/{variant}/', 'crypto_sign.h'),
             (f'faest/build/{variant}/', 'crypto_sign.c')]
    for path, file in files:
        copy(f'{FILEPATH}/{path}{file}', f'{TEST_BUILD_PATH}/{variant}/{file}')


def compile(variant, program, name, verbose):
    copy(f'{TEST_FILE_PATH}/{program}',
         f'{TEST_BUILD_PATH}/{variant}/{program}')

    link_path = f'{FILEPATH}/faest/build'

    cmd = [COMPILER, f'-L{link_path}', '-lfaest', '-o',
           name, 'crypto_sign.c', program]
    cwd = f'{TEST_BUILD_PATH}/{variant}'
    if verbose:
        process = subprocess.Popen(cmd, cwd=cwd, text=True)
    else:
        process = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
    code = process.wait()
    if code != 0:  # TODO
        exit(1)


def simplify_name(name):
    name = name.replace('massif_', '')
    name = name.replace('faest_', '')
    name = name.replace('_', '')
    name = name[:-1].upper() + name[-1]
    return name


def tool_cmd(variant, name, args):
    if args['tool'] == 'massif':
        return ['valgrind', '--tool=massif', '--stacks=yes', '--threshold=0.01',
                '--peak-inaccuracy=0.1', '--time-unit=B', '--detailed-freq=1', '--max-snapshots=1000',
                f'--massif-out-file={TEST_RESULT_MASSIF_PATH}/{simplify_name(variant)}_{name}']

    if args['tool'] == 'callgrind':
        return ['valgrind', '--tool=callgrind', f'--callgrind-out-file={TEST_RESULT_CALLGRIND_PATH}/{simplify_name(variant)}_{name}']

    return []


def start_process(variant, name, args):
    cmd = tool_cmd(variant, name, args)

    cmd += [f'{TEST_BUILD_PATH}/{variant}/{name}']

    env = os.environ.copy()
    # Linux dynamic lib path
    env['LD_LIBRARY_PATH'] = f'{FILEPATH}/faest/build'
    # MacOS dynamic lib path
    env['DYLD_LIBRARY_PATH'] = f'{FILEPATH}/faest/build'

    return subprocess.Popen(cmd, cwd=f'{TEST_BUILD_PATH}/{variant}', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env, text=True)


def run_all(args, name):
    remaining = args['variants'].copy()
    threads = []
    done = []

    # Keep specified amount of threads bussy
    while len(remaining) > 0 or len(threads) > 0:
        while len(remaining) > 0 and args['threads'] > len(threads):
            variant = remaining.pop()
            threads.append(
                (variant, start_process(variant, name, args)))

        # Print progress
        print('\r\033[96mDone:\033[0m {}, \033[96mRunning:\033[0m {}, \033[96mWaiting:\033[0m {}   '.format(
            [simplify_name(x[0]) for x in done],
            [simplify_name(x[0]) for x in threads],
            [simplify_name(x) for x in remaining]), end='')

        # Remove if done
        flag_done = []
        while not flag_done:
            flag_done = [v for v, p in threads if not p.poll() == None]
            # Avoid too busy waiting
            time.sleep(0.1)

        done += [(v, p.returncode) for v, p in threads if v in flag_done]
        threads = [(v, p) for v, p in threads if v not in flag_done]

    # Print progress
    print('\r\033[96mDone:\033[0m {}, \033[96mRunning:\033[0m {}, \033[96mWaiting:\033[0m {}   '.format(
        [simplify_name(x[0]) for x in done],
        [simplify_name(x[0]) for x in threads],
        [simplify_name(x) for x in remaining]), end='')

    # Newline
    print('')

    # Check return codes
    success = True
    for v, c in done:
        if c != 0:
            print(f'{v} returned \'{c}\'')
            success = False

    if not success:
        exit(1)


def copy_all(args):
    for v in args['variants']:
        copy_files(v)


def compile_all(args, program, name):
    for v in args['variants']:
        compile(v, program, name, args['verbose'])


def set_openssl(enable):
    if enable:
        pattern = 'if false'
        change_from = 'false'
        change_to = 'openssl.found()'
    else:
        pattern = 'if openssl.found()'
        change_from = 'openssl.found()'
        change_to = 'false'

    meson_config_file = f'{FILEPATH}/faest/meson.build'
    with open(meson_config_file, 'r') as f:
        lines = f.readlines()
        for (i, l) in enumerate(lines):
            if pattern in l:
                lines[i] = l.replace(change_from, change_to)

    with open(meson_config_file, 'w') as f:
        f.writelines(lines)


def disable_openssl():
    set_openssl(False)


def restore_openssl():
    set_openssl(True)


# ninja does not seem to always detect changes, use this to force rebuild (fx going from openssl to without)
def clean_faest():
    subprocess.run(['ninja -t clean'], cwd=f'{FILEPATH}/faest/build/',
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)


def remove_results(args):
    if args['tool'] == 'massif':
        shutil.rmtree(TEST_RESULT_MASSIF_PATH, ignore_errors=True)
    if args['tool'] == 'callgrind':
        shutil.rmtree(TEST_RESULT_CALLGRIND_PATH, ignore_errors=True)


if __name__ == '__main__':
    args = parse_args()

    if args['no-openssl']:
        print('Disabling OpenSSL')
        disable_openssl()

    if not args['no-forced-rebuild']:
        print('Forcing rebuild of FAEST')
        clean_faest()  # NOTE do this while ninja does not behave

    print('Compiling FAEST')
    compile_faest(args['verbose'])

    if args['no-openssl']:
        print('Restoring OpenSSL')
        restore_openssl()

    print('Removing old results')
    remove_results(args)
    ensure_result_folder(args)
    copy_all(args)

    for o, n in TEST_LIST:
        if o not in args['tests']:
            continue
        print(f'[Testing {o}]')

        print('> Compiling variants')
        compile_all(args, n, o)

        print(f'Running variants ({args["threads"]} thread(s))')
        run_all(args, o)

    exit(0)

    # TODO fix parsing or remove?
    print('Parsing results')
    groups = [(o.title(), o) for o, _ in TEST_LIST]

    filename = f'results{"-no-openssl" if args["no-openssl"] else ""}.md'
    parse_and_write(TEST_RESULT_MASSIF_PATH,
                    f'{TEST_RESULT_PATH}/{filename}', groups)
