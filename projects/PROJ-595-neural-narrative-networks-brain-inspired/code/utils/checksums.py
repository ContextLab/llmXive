"""
Checksum utilities for data integrity verification (T007).

Provides SHA-256 hashing of files and directories, a project-wide
checksum manifest, and integrity verification helpers.

The module is self-contained (stdlib only) so it can be imported by
any pipeline stage regardless of logging configuration.

CLI usage:
    python -m code.utils.checksums [paths...] --manifest data/checksums.txt

With no positional paths, it hashes the project's data/ tree by default.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

CHUNK_SIZE = 65536

# Directories never included in the checksum manifest.
EXCLUDED_DIR_NAMES = {"__pycache__", ".git", ".venv", "venv", ".pytest_cache"}


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file, streaming in chunks."""
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Cannot hash non-existent file: {file_path}")
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256.update(block)
    return sha256.hexdigest()


def iter_files(root: Path, recursive: bool = True) -> List[Path]:
    """List files under *root* (sorted, deterministic order)."""
    root = Path(root)
    if root.is_file():
        return [root]
    if not root.is_dir():
        raise FileNotFoundError(f"Path does not exist: {root}")
    if recursive:
        files = [
            p
            for p in root.rglob("*")
            if p.is_file()
            and not any(part in EXCLUDED_DIR_NAMES for part in p.parts)
        ]
    else:
        files = [p for p in root.iterdir() if p.is_file()]
    return sorted(files)


def compute_directory_checksums(
    dir_path: Path, recursive: bool = True, relative_to: Optional[Path] = None
) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory.

    Returns a dict mapping a path key (relative to *relative_to* if given,
    else the file name) to its hex digest.
    """
    dir_path = Path(dir_path)
    base = Path(relative_to) if relative_to is not None else dir_path
    checksums: Dict[str, str] = {}
    for fp in iter_files(dir_path, recursive=recursive):
        key = str(fp.relative_to(base)) if fp != base else fp.name
        checksums[key] = compute_sha256(fp)
    return checksums


def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load an existing JSON state/manifest file, or {} if absent/empty."""
    state_path = Path(state_path)
    if not state_path.exists():
        return {}
    try:
        with open(state_path, "r") as f:
            content = f.read().strip()
        return json.loads(content) if content else {}
    except json.JSONDecodeError as e:
        raise ValueError(f"Corrupt state file {state_path}: {e}") from e


def update_state_file(
    current_state: Dict[str, Any],
    new_checksums: Dict[str, Dict[str, str]],
    save: bool = False,
    state_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Merge *new_checksums* (dir_path -> {filename: hash}) into *current_state*.

    If save=True, writes the merged state as JSON to *state_path*.
    Returns the updated state dictionary.
    """
    updated = dict(current_state)
    for dir_path, file_checksums in new_checksums.items():
        # Flatten: merge the file checksums directly into the state
        # without double-nesting the 'checksums' key.
        for filename, hash_value in file_checksums.items():
            # Create a key like 'data/raw/file.txt' from dir_path='data/raw' and filename='file.txt'
            full_key = str(Path(dir_path) / filename)
            updated[full_key] = hash_value
    if save:
        if not state_path:
            raise ValueError("state_path required when save=True")
        state_path = Path(state_path)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(updated, f, indent=2, sort_keys=True)
    return updated


def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """Return True iff the file exists and its SHA-256 matches *expected_hash*."""
    file_path = Path(file_path)
    if not file_path.is_file():
        return False
    return compute_sha256(file_path) == expected_hash


def verify_manifest(manifest_path: Path, root: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify every entry of a flat manifest {relative_path: sha256}.

    Paths are resolved relative to *root* (default: manifest's parent's
    parent, i.e. the project root when the manifest lives in data/).
    Returns {relative_path: ok}.
    """
    manifest_path = Path(manifest_path)
    state = load_state_file(manifest_path)
    # Support flat manifests {relative_path: hash_value}.
    entries: Dict[str, str] = state
    if root is None:
        root = manifest_path.parent.parent
    results: Dict[str, bool] = {}
    for rel, expected in sorted(entries.items()):
        results[rel] = verify_file_integrity(Path(root) / rel, expected)
    return results


def batch_update_state_files(
    state_files: List[Path], new_checksums: Dict[str, Dict[str, str]]
) -> Dict[str, bool]:
    """Update several state files with the same new checksums."""
    results: Dict[str, bool] = {}
    for state_path in state_files:
        try:
            current = load_state_file(state_path)
            update_state_file(current, new_checksums, save=True, state_path=state_path)
            results[str(state_path)] = True
        except Exception as e:  # noqa: BLE001 - report per-file status
            print(f"ERROR: failed to update {state_path}: {e}", file=sys.stderr)
            results[str(state_path)] = False
    return results


def write_manifest(paths: List[Path], manifest_path: Path, root: Optional[Path] = None) -> Dict[str, str]:
    """
    Write a flat JSON manifest {relative_path: sha256} covering *paths*
    (files and/or directories). Returns the manifest dict.
    """
    manifest_path = Path(manifest_path)
    if root is None:
        root = Path.cwd()
    entries: Dict[str, str] = {}
    for p in paths:
        p = Path(p)
        for fp in iter_files(p):
            entries[str(fp.relative_to(root))] = compute_sha256(fp)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(entries, f, indent=2, sort_keys=True)
    return entries


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="SHA-256 checksum utilities")
    parser.add_argument("paths", nargs="*", help="Files/directories to hash (default: data/)")
    parser.add_argument("--manifest", default="data/checksums.txt",
                        help="Output manifest path (JSON)")
    parser.add_argument("--verify", action="store_true",
                        help="Verify an existing manifest instead of writing")
    args = parser.parse_args(argv)

    if args.verify:
        results = verify_manifest(Path(args.manifest))
        bad = [k for k, ok in results.items() if not ok]
        for k, ok in sorted(results.items()):
            print(f"{'OK ' if ok else 'FAIL'} {k}")
        print(f"{len(results) - len(bad)}/{len(results)} entries verified")
        return 1 if bad else 0

    root = Path.cwd()
    paths = [Path(p) for p in args.paths] or [root / "data"]
    for p in paths:
        if not p.exists():
            print(f"ERROR: path does not exist: {p}", file=sys.stderr)
            return 1
    entries = write_manifest(paths, Path(args.manifest), root=root)
    print(f"Wrote {len(entries)} checksums to {args.manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
