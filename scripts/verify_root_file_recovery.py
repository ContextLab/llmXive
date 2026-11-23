#!/usr/bin/env python3
"""Verify archived root files against the original Git objects without reading data.

Run from the repository root. Uses the index, so it also validates staged moves
and sparse checkouts. An accepted move preserves both file bytes and file mode.
"""
import argparse
import json
import subprocess
from pathlib import Path

MANIFEST = Path('notes/audit-20261008/root-file-recovery.json')


def tree_index(args: list[str]) -> dict[str, tuple[str, str]]:
    out = {}
    for entry in subprocess.check_output(['git', *args]).split(b'\0'):
        if not entry:
            continue
        meta, path = entry.decode().split('\t', 1)
        fields = meta.split()
        # ls-tree: mode type hash; ls-files --stage: mode hash stage
        out[path] = (fields[0], fields[2] if args[0] == 'ls-tree' else fields[1])
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-original", action="store_true",
                        help="also compare the pre-migration snapshot (requires its Git tree)")
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    before = tree_index(['ls-tree', '-rz', manifest['snapshot_commit']]) if args.check_original else None
    after = tree_index(['ls-files', '--stage', '-z'])
    failures = []
    sources = set()
    destinations = set()
    count = size = 0
    for group in manifest['groups']:
        for record in group['files']:
            old, new = record['source'], record['destination']
            expected = (record['mode'], record['git_blob'])
            if old in sources or new in destinations:
                failures.append(f'duplicate mapping: {old} -> {new}')
            sources.add(old)
            destinations.add(new)
            if before is not None and before.get(old) != expected:
                failures.append(f'original differs from manifest: {old}')
            if after.get(new) != expected:
                failures.append(f'recovered bytes/mode differ or missing: {new}')
            if old in after:
                failures.append(f'original misplaced path still tracked: {old}')
            count += 1
            size += record['bytes']
    if failures:
        print('\n'.join(failures))
        return 1
    print(f'Verified {count} byte-identical relocations ({size} bytes); no original paths remain.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
