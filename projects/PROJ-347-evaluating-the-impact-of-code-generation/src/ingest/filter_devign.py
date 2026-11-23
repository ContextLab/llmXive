"""
filter_devign.py

Filter the raw Devign (CodeXGLUE vulnerability) dataset to retain only
rows that satisfy the following criteria:
  (a) non‑empty ``code`` field,
  (b) a known ``vulnerability_label``,
  (c) language == ``Python``.
The script aborts with a clear error if fewer than five distinct
OWASP Top 10 vulnerability categories remain after filtering, or if the
resulting table contains fewer than 300 rows.

Output:
  * CSV file at ``data/processed/human_samples.csv`` with columns
    ``functionality_id,code,vulnerability_label,language``.
  * Log file at ``data/logs/filter.log`` listing distinct categories and
    row counts.
"""

import sys
import json
from pathlib import Path
from typing import List

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _detect_column(df: pd.DataFrame, candidates: List[str]) -> str | None:
    """
    Return the first column name that matches any of the candidate strings
    (case‑insensitive). If none match, return ``None``.
    """
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        cand_low = cand.lower()
        if cand_low in lower_cols:
            return lower_cols[cand_low]
    # fallback: try partial match
    for col in df.columns:
        col_low = col.lower()
        for cand in candidates:
            if cand_low in col_low:
                return col
    return None

def _ensure_output_dir(path: Path) -> None:
    """Create the parent directory of *path* if it does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Load the raw Devign JSONL file, apply filtering criteria, verify OWASP
    coverage, and write the filtered CSV and a brief log.
    """
    raw_path: Path = paths.data("raw", "devign", "devign_train.jsonl")
    if not raw_path.is_file():
        log.error(f"Raw dataset not found at {raw_path}")
        raise FileNotFoundError(f"Raw dataset missing: {raw_path}")

    # Load JSONL into a DataFrame
    try:
        df = pd.read_json(raw_path, lines=True, orient="records")
    except ValueError as e:
        log.exception(f"Failed to parse JSONL file {raw_path}: {e}")
        raise

    # ------------------------------------------------------------------
    # Identify relevant columns (be tolerant to naming variations)
    # ------------------------------------------------------------------
    code_col = _detect_column(df, ["code", "func_code", "source_code", "function_code"])
    if not code_col:
        log.error("Unable to locate a column containing the source code.")
        raise RuntimeError("Missing code column in dataset.")

    vuln_col = _detect_column(df, ["vulnerability_label", "vul_type", "vul_label", "vuln_type"])
    if not vuln_col:
        log.error("Unable to locate a column containing the vulnerability label.")
        raise RuntimeError("Missing vulnerability label column in dataset.")

    lang_col = _detect_column(df, ["language", "lang"])
    # ``language`` may be missing because the download script already filtered
    # for Python. In that case we will create a synthetic column.
    if not lang_col:
        log.info("Language column not found; assuming all rows are Python.")
        df["language"] = "python"
        lang_col = "language"

    id_col = _detect_column(df, ["functionality_id", "id", "sample_id", "func_id"])
    if not id_col:
        # Generate a sequential identifier if none exists.
        log.info("No explicit identifier column found; generating sequential IDs.")
        df["functionality_id"] = range(1, len(df) + 1)
        id_col = "functionality_id"

    # ------------------------------------------------------------------
    # Apply filtering criteria
    # ------------------------------------------------------------------
    # (a) non‑empty code
    mask_code = df[code_col].astype(str).str.strip().astype(bool)

    # (b) known vulnerability label (non‑null, non‑empty)
    mask_vuln = df[vuln_col].notna() & df[vuln_col].astype(str).str.strip().astype(bool)

    # (c) language == python (case‑insensitive)
    mask_lang = df[lang_col].astype(str).str.lower() == "python"

    filtered = df[mask_code & mask_vuln & mask_lang].copy()

    # ------------------------------------------------------------------
    # Verify minimum row count
    # ------------------------------------------------------------------
    row_count = len(filtered)
    if row_count < 300:
        log.error(
            f"Filtered dataset contains only {row_count} rows (< 300). "
            "The pipeline requires at least 300 samples."
        )
        raise RuntimeError(
            f"Insufficient rows after filtering: {row_count} (minimum 300 required)."
        )

    # ------------------------------------------------------------------
    # Verify OWASP Top‑10 coverage (≥ 5 distinct categories)
    # ------------------------------------------------------------------
    distinct_categories = filtered[vuln_col].dropna().unique()
    distinct_count = len(distinct_categories)
    if distinct_count < 5:
        log.error(
            f"Only {distinct_count} distinct vulnerability categories remain "
            f"({distinct_categories}). At least 5 are required."
        )
        raise RuntimeError(
            f"OWASP coverage insufficient: {distinct_count} distinct categories "
            "(minimum 5 required)."
        )

    # ------------------------------------------------------------------
    # Prepare final DataFrame with required column names
    # ------------------------------------------------------------------
    out_df = filtered.rename(
        columns={
            id_col: "functionality_id",
            code_col: "code",
            vuln_col: "vulnerability_label",
            lang_col: "language",
        }
    )[
        ["functionality_id", "code", "vulnerability_label", "language"]
    ]

    # ------------------------------------------------------------------
    # Write CSV output
    # ------------------------------------------------------------------
    out_path: Path = paths.data("processed", "human_samples.csv")
    _ensure_output_dir(out_path)
    out_df.to_csv(out_path, index=False)
    log.info(f"Wrote filtered dataset with {row_count} rows to {out_path}")

    # ------------------------------------------------------------------
    # Write log file summarising categories
    # ------------------------------------------------------------------
    log_path: Path = paths.data("logs", "filter.log")
    _ensure_output_dir(log_path)
    with log_path.open("w", encoding="utf-8") as f:
        f.write(f"Total rows after filtering: {row_count}\\n")
        f.write(
            f"Distinct vulnerability categories ({distinct_count}):\\n"
        )
        for cat in sorted(distinct_categories):
            f.write(f"- {cat}\\n")
    log.info(f"Filter summary written to {log_path}")

    # Successful exit
    return

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Propagate the exception to ensure a non‑zero exit status.
        log.exception("filter_devign failed")
        sys.exit(1)