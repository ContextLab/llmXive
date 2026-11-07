"""
Hygiene script for the llmXive project.

This script computes SHA‑256 hashes for all files under `data/raw/` and
`data/derived/` (excluding `data/results/` as required by Phase 0) and
writes a concise report to `data/results/hygiene_report.yaml`.

The report contains two top‑level keys:
  - `raw`: mapping of relative file paths (under `data/raw/`) → SHA‑256 hash
  - `derived`: mapping of relative file paths (under `data/derived/`) → SHA‑256 hash
  - `generated_at`: ISO‑8601 timestamp of the run

The script is deliberately **read‑only** with respect to the platform‑owned
`state/` directory. All artifacts are written inside the project's
`data/` hierarchy, satisfying the platform's constraints.
"""

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# llmxive toolkit utilities for project‑relative paths and logging
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Project‑relative directories
RAW_DIR: Path = paths.data("raw")
DERIVED_DIR: Path = paths.data("derived")
RESULTS_DIR: Path = paths.results()  # will resolve to <project>/data/results

# Output file (project‑owned)
REPORT_PATH: Path = RESULTS_DIR / "hygiene_report.yaml"


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a file in a memory‑efficient way.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as exc:
        log.error(f"Failed to hash {file_path}: {exc}")
        raise


def scan_directory(base_dir: Path) -> Dict[str, str]:
    """
    Recursively walk a directory and compute SHA‑256 hashes for all files.

    The keys in the returned dictionary are paths **relative to the
    supplied base_dir**, using POSIX style separators.

    Args:
        base_dir: Directory to scan.

    Returns:
        Mapping of relative file path → SHA‑256 hash.
    """
    hashes: Dict[str, str] = {}
    if not base_dir.exists():
        log.warning(f"Directory does not exist and will be skipped: {base_dir}")
        return hashes

    for root, _, files in os.walk(base_dir):
        for file_name in files:
            full_path = Path(root) / file_name
            rel_path = full_path.relative_to(base_dir).as_posix()
            hashes[rel_path] = compute_sha256(full_path)
            log.debug(f"Hashed {full_path} → {hashes[rel_path]}")
    return hashes


def generate_report() -> None:
    """
    Generate the hygiene report and write it to ``REPORT_PATH``.
    """
    log.info("Starting hygiene scan...")
    raw_hashes = scan_directory(RAW_DIR)
    derived_hashes = scan_directory(DERIVED_DIR)

    report_content = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "raw": raw_hashes,
        "derived": derived_hashes,
    }

    # Ensure the results directory exists
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write YAML – using the standard library ``yaml`` is not available,
    # so we emit a simple YAML representation manually.
    try:
        import yaml  # type: ignore
    except ImportError:
        log.error("PyYAML is required to write the hygiene report. Install via 'pip install pyyaml'.")
        sys.exit(1)

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(report_content, f, sort_keys=False, allow_unicode=True)

    log.info(f"Hygiene report written to {REPORT_PATH}")
    log.info(f"Processed {len(raw_hashes)} raw files and {len(derived_hashes)} derived files.")


if __name__ == "__main__":
    try:
        generate_report()
    except Exception as e:
        log.error(f"Hygiene script failed: {e}")
        sys.exit(1)