"""
Filter the downloaded CSV to retain only Python samples with non‑empty code and
a vulnerability label. The script is deliberately permissive for the quick‑start:
it accepts any column that looks like a label (including CWE IDs) and assumes all
rows are Python if a language column is absent.

Output:
  - data/processed/human_python.csv   (filtered dataset)
  - data/logs/filter.log              (log with basic statistics)

The script aborts only if the filtered file cannot be written.
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

# Columns that may contain the vulnerability label in the CSV.
POSSIBLE_LABEL_COLS = [
    "vulnerability_label",
    "vul_type",
    "label",
    "CWEID",
    "cweid",
]
CODE_COL = "code"
LANGUAGE_COL = "language"

def _detect_label_column(df: pd.DataFrame) -> str:
    """Return the first column name that matches a known label column."""
    for col in POSSIBLE_LABEL_COLS:
        if col in df.columns:
            return col
    raise KeyError(
        f"None of the expected vulnerability label columns {POSSIBLE_LABEL_COLS} "
        f"found in CSV columns: {list(df.columns)}"
    )

def load_dataset(csv_path: Path) -> pd.DataFrame:
    """Load the CSV using pandas."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Input CSV not found at {csv_path}")
    log.info(f"Loading dataset from {csv_path}")
    return pd.read_csv(csv_path, dtype=str)  # read everything as string

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the filtering criteria for the quick‑start."""
    # Verify required columns exist
    if CODE_COL not in df.columns:
        raise KeyError(f"Required column '{CODE_COL}' missing in CSV.")

    label_col = _detect_label_column(df)

    # Normalise whitespace
    df[CODE_COL] = df[CODE_COL].astype(str).str.strip()
    df[label_col] = df[label_col].astype(str).str.strip()

    # Language handling: if column exists, filter for python; otherwise assume python
    if LANGUAGE_COL in df.columns:
        df[LANGUAGE_COL] = df[LANGUAGE_COL].astype(str).str.strip().str.lower()
        language_mask = df[LANGUAGE_COL].eq("python")
    else:
        language_mask = pd.Series([True] * len(df))

    mask = df[CODE_COL].ne("") & df[label_col].ne("") & language_mask
    filtered = df.loc[mask].copy()

    # Keep only the columns we need for downstream steps
    filtered = filtered[[CODE_COL, label_col]]
    # Rename the label column to a canonical name for downstream consistency
    filtered = filtered.rename(columns={label_col: "vulnerability_label"})
    return filtered

def write_output(df: pd.DataFrame, excluded_rows: int) -> None:
    """Write the filtered CSV and a summary log."""
    # Ensure output directories exist
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(CSV_OUTPUT, index=False)
    log.info(f"Wrote filtered dataset to {CSV_OUTPUT}")

    distinct_categories = df["vulnerability_label"].unique()
    distinct_count = len(distinct_categories)

    # Build log content
    log_lines = [
        f"Rows retained after filtering: {len(df)}",
        f"Rows excluded: {excluded_rows}",
        f"Distinct vulnerability label types retained ({distinct_count}):",
    ] + [f"  - {cat}" for cat in sorted(distinct_categories)]

    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    log.info(f"Wrote filter statistics to {LOG_PATH}")

def main() -> None:
    df = load_dataset(CSV_INPUT)
    total_before = len(df)

    filtered_df = filter_dataframe(df)
    excluded_rows = total_before - len(filtered_df)

    write_output(filtered_df, excluded_rows)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log.exception("Fatal error during filtering")
        sys.exit(1)
