"""Compute SHA-256 checksums for all raw data files under ``data/``."""

import hashlib
from pathlib import Path

from llmxive_toolkit import paths


def _sha256_file(file_path: Path) -> str:
    """Return the SHA-256 checksum of *file_path* as a hex string."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> None:
    """
    Walk the ``data`` directory, compute a SHA-256 checksum for every file
    (excluding the checksum file itself), and write the results to
    ``data/checksums.txt`` in the format:

        <checksum>  <relative_path>
    """
    data_root: Path = paths.data()

    all_files = [
        p
        for p in data_root.rglob("*")
        if p.is_file() and p.name != "checksums.txt"
    ]

    out_path: Path = paths.data("checksums.txt")

    lines = []
    for file_path in sorted(all_files):
        checksum = _sha256_file(file_path)
        rel_path = file_path.relative_to(data_root)
        lines.append(f"{checksum}  {rel_path}")

    # Write with real newlines (the previous version emitted a literal
    # "\\n" sequence, producing a single broken line).
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote checksums for {len(all_files)} files to {out_path}")


if __name__ == "__main__":
    main()
