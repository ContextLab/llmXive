"""
code/run_pipeline_with_checksum.py
---------------------------------

This script is the corrected entry point referenced in the quickstart
documentation. It orchestrates the full analysis pipeline while
performing a checksum verification step on the raw dataset.

The script performs the following high‑level actions:

1. Initialise logging and reproducibility seeds.
2. Download and validate the raw HEA dataset (using ``fetch_heas``).
3. Compute the SHA‑256 checksum of the resulting ``data/raw/heas_raw.csv``
   and record it in the project state file.
4. Run the remaining pipeline stages (pre‑processing, descriptor
   generation, modelling, evaluation, etc.) via the existing
   ``code/T015_generate.py`` orchestrator.
5. Write a final manifest summarising artefacts and package versions.

The script accepts two optional CLI arguments:
    --seed       Random seed for deterministic execution (default: 42)
    --output-dir Directory where final artefacts (reports, plots, etc.)
                 will be written (default: ``output/``).

All paths are resolved relative to the project root using the
``llmxive_toolkit.paths`` helpers.
"""

import argparse
import sys
import os
import json
import hashlib
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Project‑specific imports
from data.fetch_heas import fetch_heas
from T061_compute_checksum import record_checksum
from T015_generate import main as generate_main
from utils.logging import set_seeds

logger = get_logger(__name__)

def _build_manifest(output_dir: Path) -> dict:
    """
    Build a minimal manifest containing SHA‑256 checksums for the raw
    dataset and the processed descriptor CSV, along with package versions
    and timestamps.
    """
    manifest = {
        "run_id": hashlib.sha256(os.urandom(16)).hexdigest(),
        "timestamp": Path.cwd().stat().st_mtime,
        "seeds": {"global": int(os.getenv("HEA_SEED", "42"))},
        "artifacts": {},
    }

    raw_path = paths.data("raw", "heas_raw.csv")
    desc_path = paths.data("processed", "hea_descriptors.csv")

    for p in (raw_path, desc_path):
        if p.is_file():
            manifest["artifacts"][str(p)] = {
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "size_bytes": p.stat().st_size,
            }

    # Record package versions (for the core dependencies that are guaranteed
    # to be present in the execution environment).
    try:
        import pandas
        import numpy
        import sklearn
        manifest["packages"] = {
            "pandas": pandas.__version__,
            "numpy": numpy.__version__,
            "scikit-learn": sklearn.__version__,
        }
    except Exception:
        manifest["packages"] = {}

    return manifest

def run_pipeline(seed: int, output_dir: Path) -> int:
    """
    Execute the full pipeline. Returns 0 on success, non‑zero on failure.
    """
    logger.info(f"Starting pipeline with seed={seed}, output_dir={output_dir}")

    # 1. Set deterministic seeds.
    set_seeds(seed)

    # 2. Ensure raw dataset is present and validated.
    try:
        raw_path = fetch_heas()
    except Exception as exc:
        logger.error(f"Failed to obtain raw dataset: {exc}")
        return 1

    # 3. Record checksum of the raw dataset.
    try:
        record_checksum(descriptor_path=Path(raw_path))
    except Exception as exc:
        logger.error(f"Checksum recording failed: {exc}")
        return 1

    # 4. Run descriptor generation and status writing (T015).
    try:
        generate_main()
    except Exception as exc:
        logger.error(f"Descriptor generation failed: {exc}")
        return 1

    # 5. Record checksum of the processed descriptor CSV.
    try:
        record_checksum()
    except Exception as exc:
        logger.error(f"Checksum recording for descriptor CSV failed: {exc}")
        return 1

    # 6. Write manifest.
    manifest = _build_manifest(output_dir)
    manifest_path = output_dir / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Pipeline completed successfully. Manifest written to {manifest_path}")
    return 0

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the full HEA analysis pipeline.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/",
        help="Directory to store final artefacts (manifest, report, etc.)",
    )
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir)
    return run_pipeline(seed=args.seed, output_dir=output_dir)

if __name__ == "__main__":
    sys.exit(main())