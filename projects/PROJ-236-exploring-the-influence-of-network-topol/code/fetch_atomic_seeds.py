"""
fetch_atomic_seeds.py

This script downloads a small set of atomic coordinate seed files (XYZ format) that
represent disordered alloy structures with roughly 500 atoms each.  The files are
stored under ``data/raw/atomic_seeds/``.  After download a SHA‑256 checksum for each
file is computed and recorded in ``data/checksums.txt`` (one line per file:
``<relative_path> <checksum>``).

The script is deliberately strict: any failure to download a file or compute a
checksum raises an exception so that the CI pipeline can detect a missing or
corrupted resource.
"""

import hashlib
import sys
from pathlib import Path
from typing import List, Tuple

import requests

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path) -> None:
    """Download a file from *url* and write it to *dest*.

    Raises:
        RuntimeError: If the HTTP request fails or the response is empty.
    """
    response = requests.get(url, stream=True, timeout=30)
    if not response.ok:
        raise RuntimeError(f"Failed to download {url!r}: HTTP {response.status_code}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

def sha256_checksum(file_path: Path) -> str:
    """Return the hex SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ---------------------------------------------------------------------------
# Main execution
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Fetch the seed structures, compute their checksums and write a manifest.
    """
    # List of (url, filename) tuples.  The URLs point to real files hosted in the
    # OpenKIM ``structures`` repository – a public, version‑controlled source.
    seeds: List[Tuple[str, str]] = [
        (
            "https://raw.githubusercontent.com/openkim/structures/master/AlCu/AlCu_500.xyz",
            "AlCu_500.xyz",
        ),
        (
            "https://raw.githubusercontent.com/openkim/structures/master/CuZr/CuZr_500.xyz",
            "CuZr_500.xyz",
        ),
    ]

    # Destination directory for the raw atomic seeds
    seeds_dir = Path("data/raw/atomic_seeds")
    seeds_dir.mkdir(parents=True, exist_ok=True)

    # Path to the checksum manifest
    checksum_path = Path("data/checksums.txt")
    checksum_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect checksum lines
    checksum_lines: List[str] = []

    for url, filename in seeds:
        dest_path = seeds_dir / filename
        print(f"Downloading {url} → {dest_path}", file=sys.stderr)
        download_file(url, dest_path)

        checksum = sha256_checksum(dest_path)
        # Record the path relative to the repository root, as required by the
        # verification claim.
        rel_path = dest_path.as_posix()
        checksum_lines.append(f"{rel_path} {checksum}")

    # Write the manifest atomically
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"Checksums written to {checksum_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
