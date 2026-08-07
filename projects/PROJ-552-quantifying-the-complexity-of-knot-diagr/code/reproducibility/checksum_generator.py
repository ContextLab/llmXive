"""Generate SHA-256 checksums for all files under the data directory.

The script walks ``data/`` recursively, computes a SHA-256 hash for each
regular file, and writes a markdown table to
``docs/reproducibility/checksums.md``. The format is:

| Relative Path | SHA-256 |
|---|---|
| data/raw/knot_atlas_raw.json | <hash> |

This file is part of the reproducibility run‑book and must exist.
"""
import hashlib
from pathlib import Path

def _sha256_of_file(path: Path) -> str:
    """Return the hex SHA‑256 digest of *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    data_root = Path("data")
    output_md = Path("docs/reproducibility/checksums.md")

    if not data_root.is_dir():
        raise FileNotFoundError(f"Data directory {data_root!s} does not exist")

    rows = []
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            rel = file_path.relative_to(Path.cwd())
            checksum = _sha256_of_file(file_path)
            rows.append((str(rel), checksum))

    # Sort rows for reproducibility
    rows.sort(key=lambda x: x[0])

    with output_md.open("w", encoding="utf-8") as out:
        out.write("| Relative Path | SHA-256 |\n")
        out.write("|---|---|\n")
        for rel, cs in rows:
            out.write(f"| {rel} | {cs} |\n")

    print(f"Wrote checksums for {len(rows)} files to {output_md}")


if __name__ == "__main__":
    main()
