"""
Report generation module for the molecular complexity degradation study.
Handles reproducibility checks, metadata logging, and final report assembly.
"""
import os
import sys
import json
import hashlib
import importlib.metadata
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

# Import from project modules based on provided API surface
from logging_config import get_logger, log_pipeline_start, log_pipeline_complete

logger = get_logger(__name__)

# Constants
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = DATA_DIR / "outputs"
REPORT_PATH = Path("results_report.md")
REPRODUCIBILITY_PATH = PROCESSED_DIR / "reproducibility.json"

# Dataset metadata (from T012/T017)
DATASET_URL = "https://huggingface.co/datasets/Synthyra/FDA-Approved-Drugs"
DATASET_NAME = "Synthyra/FDA-Approved-Drugs"


def calculate_file_hash(file_path: Path) -> Optional[str]:
    """
    Calculate SHA-256 hash of a file.
    Returns None if file does not exist.
    """
    if not file_path.exists():
        logger.warning(f"File not found for hashing: {file_path}")
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return None


def get_package_version(package_name: str) -> str:
    """
    Safely retrieve the version of an installed package.
    """
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "NOT_INSTALLED"


def collect_reproducibility_metadata() -> Dict[str, Any]:
    """
    Collect all metadata required for reproducibility:
    - Code versions (RDKit, scikit-learn, pandas, numpy)
    - Dataset URL and name
    - Retrieval date (current timestamp)
    - File hashes for key data artifacts
    """
    logger.info("Collecting reproducibility metadata...")

    # 1. Software Versions
    versions = {
        "rdkit": get_package_version("rdkit"),
        "scikit-learn": get_package_version("scikit-learn"),
        "pandas": get_package_version("pandas"),
        "numpy": get_package_version("numpy"),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }

    # 2. Dataset Metadata
    dataset_info = {
        "url": DATASET_URL,
        "name": DATASET_NAME,
        "retrieval_date": datetime.utcnow().isoformat() + "Z",
    }

    # 3. File Hashes
    # We assume these files exist based on completed tasks T017, T026, T032-T034
    files_to_hash = {
        "merged_dataset": PROCESSED_DIR / "merged_drugs.csv",
        "analysis_results": PROCESSED_DIR / "analysis_results.json",
        "scatter_plot": OUTPUTS_DIR / "scatter_tpsa_vs_half_life.png",
        "residual_plot": OUTPUTS_DIR / "residuals.png",
        "qq_plot": OUTPUTS_DIR / "qq_plot.png",
    }

    hashes = {}
    for key, path in files_to_hash.items():
        h = calculate_file_hash(path)
        if h:
            hashes[key] = h
        else:
            hashes[key] = "MISSING"
            logger.warning(f"Missing file for hash calculation: {path}")

    return {
        "software_versions": versions,
        "dataset": dataset_info,
        "file_hashes": hashes,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def save_reproducibility_report(metadata: Dict[str, Any]) -> None:
    """
    Save the reproducibility metadata to a JSON file.
    """
    if not PROCESSED_DIR.exists():
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with open(REPRODUCIBILITY_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Reproducibility report saved to {REPRODUCIBILITY_PATH}")


def append_reproducibility_to_markdown(metadata: Dict[str, Any]) -> None:
    """
    Append the reproducibility section to the existing results_report.md.
    If the file doesn't exist, create it with the section.
    """
    if not REPORT_PATH.exists():
        logger.warning(f"{REPORT_PATH} not found. Creating a new report with reproducibility section.")
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write("# Molecular Complexity and Degradation Rates Report\n\n")
            f.write("## Reproducibility Metadata\n\n")
            f.write("```json\n")
            json.dump(metadata, f, indent=2)
            f.write("\n```\n")
        return

    # Read existing content
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Append section
    reproducibility_section = "\n\n## Reproducibility Metadata\n\n"
    reproducibility_section += "The following metadata ensures the reproducibility of this study:\n\n"
    reproducibility_section += "```json\n"
    reproducibility_section += json.dumps(metadata, indent=2)
    reproducibility_section += "\n```\n"

    with open(REPORT_PATH, "a", encoding="utf-8") as f:
        f.write(reproducibility_section)

    logger.info(f"Reproducibility section appended to {REPORT_PATH}")


def main() -> None:
    """
    Main entry point for T035: Implement reproducibility check.
    1. Collect metadata (versions, URLs, hashes).
    2. Save to JSON.
    3. Append to results_report.md.
    """
    log_pipeline_start("T035-Reproducibility")

    try:
        # 1. Collect Metadata
        metadata = collect_reproducibility_metadata()

        # 2. Save JSON Report
        save_reproducibility_report(metadata)

        # 3. Append to Markdown Report
        append_reproducibility_to_markdown(metadata)

        logger.info("T035 Reproducibility check completed successfully.")
        log_pipeline_complete("T035-Reproducibility")

    except Exception as e:
        logger.error(f"Failed to complete T035: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()