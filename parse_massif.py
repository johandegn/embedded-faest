# This script is used to parse massif output files and create a markdown table.
import os


class Snapshot:
    def __init__(self, snapshot, usefull_heap, extra_heap, stack):
        self.snapshot = int(snapshot)
        self.usefull_heap = int(usefull_heap)
        self.extra_heap = int(extra_heap)
        self.stack = int(stack)
        self.total = self.usefull_heap + self.extra_heap + self.stack

    def __str__(self):
        return f'snapshot: {self.snapshot}, Total: {self.total}'


class File:
    def __init__(self, name, snapshots):
        self.name = name
        self.snapshots = snapshots

    def __str__(self):
        return f'File: {self.name}, Total peak: {self.max_memory()}'

    def max_memory(self):
        return max([s.total for s in self.snapshots])


def parse_chunk(chunk):
    lines = chunk.split()
    assert (lines[0].startswith('snapshot='))
    assert (lines[3].startswith('mem_heap_B='))
    assert (lines[4].startswith('mem_heap_extra_B='))
    assert (lines[5].startswith('mem_stacks_B='))

    snapshot = lines[0].split('=')[1]
    usefull_heap = lines[3].split('=')[1]
    extra_heap = lines[4].split('=')[1]
    stack = lines[5].split('=')[1]
    return Snapshot(snapshot, usefull_heap, extra_heap, stack)


def filepath_to_simple_name(filepath):
    name = os.path.basename(filepath)
    idx = name.find('_')
    name = name[:idx]
    return name


def parse_file(filename):
    with open(filename, 'r') as f:
        content = f.read()
        delim = 'snapshot'
        chunks = content.split(delim)
        chunks = [delim + c for c in chunks[1:]]
        snapshots = [parse_chunk(c) for c in chunks]

        name = filepath_to_simple_name(filename)
        return File(name, snapshots)


def parse_folder(dir_path, endswith):
    files = []
    for element in os.listdir(dir_path):
        path = os.path.join(dir_path, element)
        if not os.path.isfile(path):
            continue
        if not element.endswith(endswith):
            continue

        files.append(parse_file(path))
    return files


def write_markdown_table(grouped_files, outpath):
    header = '| Variant |'
    separator = '|:-------:|'
    for name, _ in grouped_files:
        header += f' {name} |'
        separator += f' {len(name) * "-"}:|'

    with open(outpath, 'w') as wf:
        wf.write(header + '\n')
        wf.write(separator + '\n')

        variants = [f.name for f in grouped_files[0][1]]
        variants = sorted(variants, key=lambda v: (v[-1], v[:-1]))

        for v in variants:
            wf.write(f'| {v} |')
            for name, files in grouped_files:
                for f in files:
                    if f.name == v:
                        wf.write(f' {f.max_memory()//1000:,}kB |')
                        break
            wf.write('\n')


def parse_and_write(dir_path, outpath, groups):
    grouped_files = []
    for name, endswith in groups:
        grouped_files.append((name, parse_folder(dir_path, endswith)))
    write_markdown_table(grouped_files, outpath)


if __name__ == '__main__':
    print('This script should not be run directly')
    exit(1)
