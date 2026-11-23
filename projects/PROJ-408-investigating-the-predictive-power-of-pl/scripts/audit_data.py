"""
Audit script for T042: Data Retention Audit.

This script provides an independent verification of SC-003 (Retention Threshold)
by parsing the original species list and the processed phylogenetic distance matrix.
It writes a human‑readable report to ``output/reports/retention_audit.txt`` and
exits with status 0 for PASS and 1 for FAIL.
"""
import sys
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Set, Tuple

# Add project root to sys.path so that sibling modules can be imported
project_root = Path(__file__).resolve().parents[1]  # scripts/ -> project root
sys.path.insert(0, str(project_root))

from config import load_config
from logging_config import setup_logging

def load_species_list(species_list_path: Path) -> Set[str]:
    """
    Load the target species list from ``data/raw/species_list.txt``.
    Returns a set of scientific names (the third column).
    """
    if not species_list_path.is_file():
        raise FileNotFoundError(f"Species list not found at {species_list_path}")

    species: Set[str] = set()
    with species_list_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                species.add(parts[2])
    return species

def load_retained_species(matrix_path: Path) -> Set[str]:
    """
    Load the set of species that made it through the pipeline.
    The function expects a CSV distance matrix with the first column
    containing species names (header may be ``species`` or similar).

    If the matrix does not exist, an empty set is returned.
    """
    if not matrix_path.is_file():
        return set()

    retained: Set[str] = set()
    with matrix_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # skip header
        for row in reader:
            if row:
                retained.add(row[0].strip())
    return retained

def calculate_retention(
    target: Set[str], retained: Set[str]
) -> Tuple[float, Set[str], Set[str]]:
    """
    Compute retention percentage and the missing/kept subsets.

    Returns:
        retention_pct – percentage of target species retained
        missing – species in the target list that were not retained
        kept – intersection of target and retained species
    """
    if not target:
        return 0.0, set(), set()

    kept = target & retained
    missing = target - retained
    retention_pct = (len(kept) / len(target)) * 100.0
    return retention_pct, missing, kept

def write_report(
    output_path: Path,
    target_count: int,
    retained_count: int,
    retention_pct: float,
    status: str,
    missing: Set[str],
    kept: Set[str],
) -> None:
    """
    Write a formatted audit report.
    """
    with output_path.open("w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("DATA RETENTION AUDIT REPORT\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Target Species Count   : {target_count}\n")
        f.write(f"Retained Species Count : {retained_count}\n")
        f.write(f"Retention Percentage   : {retention_pct:.2f}%\n")
        f.write(f"Threshold (80%)        : 80.00%\n")
        f.write(f"Status                 : {status}\n\n")

        if missing:
            f.write("MISSING SPECIES (target but not retained):\n")
            for sp in sorted(missing):
                f.write(f"  - {sp}\n")
            f.write("\n")

        f.write("RETAINED SPECIES (used in downstream analysis):\n")
        for sp in sorted(kept):
            f.write(f"  - {sp}\n")
        f.write("\n")
        f.write("=" * 60 + "\n")
        f.write(f"AUDIT RESULT: {status}\n")
        f.write("=" * 60 + "\n")

def main() -> int:
    """
    Entry point for the audit script.

    Returns:
        0 if retention meets or exceeds the threshold,
        1 otherwise.
    """
    # Initialise logging
    logger: logging.Logger = setup_logging()
    logger.info("Starting Data Retention Audit (T042)")

    # Load configuration (primarily for directory paths)
    config = load_config()

    # Define paths relative to the project root
    species_list_path = config.project_root / "data" / "raw" / "species_list.txt"
    matrix_path = config.project_root / "data" / "processed" / "phylo_dist_matrix.csv"
    report_path = config.project_root / "output" / "reports" / "retention_audit.txt"

    # Ensure the output directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load the target species list
        logger.info(f"Loading target species from %s", species_list_path)
        target_species = load_species_list(species_list_path)
        logger.info("Target species count: %d", len(target_species))

        # 2. Load the retained species from the distance matrix
        logger.info(f"Loading retained species from %s", matrix_path)
        retained_species = load_retained_species(matrix_path)
        logger.info("Retained species count: %d", len(retained_species))

        # 3. Compute retention statistics
        retention_pct, missing, kept = calculate_retention(
            target_species, retained_species
        )
        threshold = config.retention_threshold * 100.0  # convert to percent
        status = "PASS" if retention_pct >= threshold else "FAIL"
        logger.info("Retention: %.2f%% (threshold %.2f%%) -> %s", retention_pct, threshold, status)

        # 4. Write the audit report
        write_report(
            output_path=report_path,
            target_count=len(target_species),
            retained_count=len(retained_species),
            retention_pct=retention_pct,
            status=status,
            missing=missing,
            kept=kept,
        )
        logger.info("Audit report written to %s", report_path)

        return 0 if status == "PASS" else 1

    except FileNotFoundError as e:
        logger.error("Critical file missing: %s", e)
        # Write a minimal failure report
        report_path.write_text(f"AUDIT FAILED: {e}\n", encoding="utf-8")
        return 1
    except Exception as e:
        logger.exception("Unexpected error during audit")
        raise

if __name__ == "__main__":
    sys.exit(main())
