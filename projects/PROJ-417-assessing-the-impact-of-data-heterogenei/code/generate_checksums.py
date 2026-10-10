"""
Generate SHA‑256 checksums for all final artifacts produced by the pipeline
and record them in ``state/artifact_hashes.yaml``.

The script is intended to be run after the full pipeline execution
(T001 → T010). It walks the ``data/results`` directory, computes a
SHA‑256 hash for each file (recursively), and writes a YAML mapping of
relative file paths to their hexadecimal digests.

The output file is created under the ``state`` directory, which is
automatically created if missing. Existing checksum files are
overwritten.

This script is deliberately lightweight and depends only on the
Python standard library and ``pyyaml`` (already declared in
``code/requirements.txt``).
"""

import hashlib
import sys
from pathlib import Path

import yaml

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    hasher = hashlib.sha256()
    # Read in binary mode in chunks to handle large files efficiently.
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def collect_results_files(results_dir: Path) -> dict[str, str]:
    """
    Walk ``results_dir`` and compute a SHA‑256 hash for every file.

    Returns
    -------
    dict
        Mapping of POSIX‑style relative paths (relative to the repository
        root) to their hex digests.
    """
    if not results_dir.is_dir():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    hashes: dict[str, str] = {}
    for file_path in results_dir.rglob("*"):
        if file_path.is_file():
            # Store paths relative to the repository root (POSIX style)
            rel_path = file_path.as_posix()
            hashes[rel_path] = compute_sha256(file_path)
    return hashes


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main() -> int:
    """
    Compute checksums for all files under ``data/results`` and write the
    mapping to ``state/artifact_hashes.yaml``.

    Returns
    -------
    int
        Exit code (0 on success, non‑zero on failure).
    """
    repo_root = Path(__file__).resolve().parents[1]  # project root
    results_dir = repo_root / "data" / "results"
    state_dir = repo_root / "state"
    output_path = state_dir / "artifact_hashes.yaml"

    try:
        state_dir.mkdir(parents=True, exist_ok=True)

        hashes = collect_results_files(results_dir)

        # Write YAML with sorted keys for reproducibility
        with output_path.open("w", encoding="utf-8") as out_file:
            yaml.safe_dump(
                hashes,
                out_file,
                default_flow_style=False,
                sort_keys=True,
                allow_unicode=True,
            )

        print(f"✅ Checksums written to {output_path}")
        return 0
    except Exception as exc:
        print(f"❌ Error while generating checksums: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())