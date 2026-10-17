"""
T003: Apply the strict-tolerance outlier rule (FR-004) to every row of
data/processed/mc_results.csv and write
data/processed/validated_sweep_results.csv with an additional boolean
column `outlier_flag` recomputed from `eigenvalue_top` and
`empirical_bulk_edge`.

FR-004 rule: outlier_flag = (eigenvalue_top > empirical_bulk_edge + 0.05)

The script is a pure post-processing step over the real ARPACK
measurements recorded by T002 (threshold_sweep.py). No synthetic data
is generated; if the input file is missing the script fails loudly.
"""
import argparse
import csv
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_LOGS = PROJECT_ROOT / "data" / "logs"

# FR-004 strict tolerance for outlier detection
OUTLIER_TOLERANCE = 0.05

INPUT_CSV = DATA_PROCESSED / "mc_results.csv"
OUTPUT_CSV = DATA_PROCESSED / "validated_sweep_results.csv"

def setup_logging() -> logging.Logger:
    DATA_LOGS.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("validate_sweep_results")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fmt = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        fh = logging.FileHandler(DATA_LOGS / "validate_sweep_results.log")
        fh.setFormatter(fmt)
        logger.addHandler(sh)
        logger.addHandler(fh)
    return logger

def compute_outlier_flag(eigenvalue_top: float, empirical_bulk_edge: float,
                         tolerance: float = OUTLIER_TOLERANCE) -> bool:
    """FR-004: an eigenvalue is an outlier iff it exceeds the empirical
    bulk edge by strictly more than the tolerance 0.05."""
    return float(eigenvalue_top) > float(empirical_bulk_edge) + tolerance

def validate_sweep_results(input_path: Path = INPUT_CSV,
                           output_path: Path = OUTPUT_CSV,
                           tolerance: float = OUTLIER_TOLERANCE) -> int:
    """Read mc_results.csv, recompute outlier_flag per row, write
    validated_sweep_results.csv. Returns the number of rows written."""
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Run T002 (code/analysis/threshold_sweep.py) first."
        )

    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    required = ["eigenvalue_top", "empirical_bulk_edge"]
    missing = [c for c in required if c not in fieldnames]
    if missing:
        raise ValueError(
            f"Input CSV is missing required columns: {missing}"
        )
    if len(rows) == 0:
        raise ValueError(f"Input CSV {input_path} contains no data rows.")

    if "outlier_flag" not in fieldnames:
        fieldnames = fieldnames + ["outlier_flag"]

    out_rows = []
    n_outliers = 0
    for row in rows:
        flag = compute_outlier_flag(
            row["eigenvalue_top"], row["empirical_bulk_edge"], tolerance
        )
        row["outlier_flag"] = "True" if flag else "False"
        n_outliers += int(flag)
        out_rows.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    logger = logging.getLogger("validate_sweep_results")
    logger.info(
        f"Wrote {len(out_rows)} rows to {output_path} "
        f"({n_outliers} outliers, {len(out_rows) - n_outliers} non-outliers)"
    )
    if len(out_rows) != len(rows):
        raise RuntimeError("Row count mismatch between input and output.")
    return len(out_rows)

def main() -> int:
    global logger
    logger = setup_logging()
    logger.info(
        "T003: applying FR-004 outlier rule "
        "(eigenvalue_top > empirical_bulk_edge + 0.05)"
    )
    try:
        n = validate_sweep_results()
        logger.info(f"T003 completed: {n} validated rows.")
        return 0
    except Exception as e:
        logger.error(f"T003 failed: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
