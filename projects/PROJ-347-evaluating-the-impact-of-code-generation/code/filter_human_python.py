"""
Filter the Devign dataset to retain only Python samples with non‑empty code and
vulnerability labels, and ensure the filtered ground‑truth contains at least five
distinct OWASP vulnerability types.

Output:
  - data/processed/human_python.csv   (filtered dataset)
  - data/logs/filter.log              (log with statistics)

The script aborts with a RuntimeError if the distinct OWASP category count is
below the required threshold.
"""
import sys
import pandas as pd
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
CSV_INPUT = paths.data("raw", "devign", "devign.csv")
CSV_OUTPUT = paths.data("processed", "human_python.csv")
LOG_PATH = paths.data("logs", "filter.log")
REQUIRED_DISTINCT_TYPES = 5

# Column names expected in the Devign CSV. Adjust if the dataset schema changes.
CODE_COL = "code"
VULN_LABEL_COL = "vulnerability_label"
LANGUAGE_COL = "language"

def load_dataset(csv_path: Path) -> pd.DataFrame:
    """Load the Devign CSV using pandas."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Input CSV not found at {csv_path}")
    log.info(f"Loading Devign dataset from {csv_path}")
    return pd.read_csv(csv_path, dtype=str)  # read everything as string

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the filtering criteria described in the task."""
    missing_cols = [
        c for c in (CODE_COL, VULN_LABEL_COL, LANGUAGE_COL) if c not in df.columns
    ]
    if missing_cols:
        raise KeyError(f"Required column(s) missing in CSV: {missing_cols}")

    # Strip whitespace and treat empty strings as NaN
    df[CODE_COL] = df[CODE_COL].astype(str).str.strip()
    df[VULN_LABEL_COL] = df[VULN_LABEL_COL].astype(str).str.strip()
    df[LANGUAGE_COL] = df[LANGUAGE_COL].astype(str).str.strip().str.lower()

    mask = (
        df[CODE_COL].ne("") &
        df[VULN_LABEL_COL].ne("") &
        df[LANGUAGE_COL].eq("python")
    )
    filtered = df[mask].copy()
    return filtered

def write_output(df: pd.DataFrame) -> None:
    """Write the filtered CSV and a summary log."""
    # Ensure output directories exist
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(CSV_OUTPUT, index=False)
    log.info(f"Wrote filtered dataset to {CSV_OUTPUT}")

    total_rows = len(df) + excluded_rows
    distinct_categories = df[VULN_LABEL_COL].unique()
    distinct_count = len(distinct_categories)

    # Build log content
    log_lines = [
        f"Total rows in original CSV: {total_rows}",
        f"Rows retained after filtering: {len(df)}",
        f"Rows excluded: {excluded_rows}",
        f"Distinct OWASP vulnerability types retained ({distinct_count}):",
    ] + [f"  - {cat}" for cat in sorted(distinct_categories)]

    log_text = "\n".join(log_lines)
    LOG_PATH.write_text(log_text, encoding="utf-8")
    log.info(f"Wrote filter statistics to {LOG_PATH}")

def main() -> None:
    global excluded_rows  # used for logging after filtering
    df = load_dataset(CSV_INPUT)
    total_before = len(df)

    filtered_df = filter_dataframe(df)
    excluded_rows = total_before - len(filtered_df)

    distinct_categories = filtered_df[VULN_LABEL_COL].unique()
    if len(distinct_categories) < REQUIRED_DISTINCT_TYPES:
        raise RuntimeError(
            f"Filtered dataset contains only {len(distinct_categories)} distinct "
            f"OWASP vulnerability types, which is fewer than the required "
            f"{REQUIRED_DISTINCT_TYPES}."
        )

    write_output(filtered_df)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Fatal error during filtering")
        sys.exit(1)