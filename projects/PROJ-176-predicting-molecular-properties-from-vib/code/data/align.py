"""
Align QM9 properties with IR spectra on InChIKey.
Reads the parquet files produced by the download step (or downloads them if missing),
performs an inner join, logs the number of matched and discarded molecules,
and writes a JSON report to ``data/processed/alignment_report.json``.
"""

import json
import logging
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

# Configure logger
log = get_logger(__name__)

def _ensure_raw_file(file_path: Path, dataset_name: str, split: str = "train") -> None:
    """
    Ensure that a raw parquet file exists.
    If it does not, download the dataset from HuggingFace and write it to ``file_path``.
    """
    if file_path.is_file():
        return

    log.info(f"{file_path.name} not found – downloading {dataset_name} dataset (split={split})")
    # Load the specified split; many datasets expose a 'train' split that contains the full data.
    ds = load_dataset(dataset_name, split=split)
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_parquet(str(file_path), engine="pyarrow")
    log.info(f"Saved {dataset_name} (split={split}) to {file_path}")

def load_parquet(file_path: Path) -> pd.DataFrame:
    """Load a parquet file using pandas."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Expected parquet file not found: {file_path}")
    return pd.read_parquet(file_path, engine="pyarrow")

def align_datasets(
    qm9_df: pd.DataFrame,
    ir_df: pd.DataFrame,
    key: str = "InChIKey",
) -> pd.DataFrame:
    """
    Perform an inner join on ``key`` (default ``InChIKey``).

    Returns:
        pd.DataFrame: The aligned dataset containing only rows present in both inputs.
    """
    if key not in qm9_df.columns:
        raise KeyError(f"{key} not found in QM9 dataframe columns: {list(qm9_df.columns)}")
    if key not in ir_df.columns:
        raise KeyError(f"{key} not found in IR spectra dataframe columns: {list(ir_df.columns)}")

    merged = pd.merge(qm9_df, ir_df, on=key, how="inner")
    return merged

def write_report(matched: int, discarded: int, output_path: Path) -> None:
    """Write the alignment report as JSON."""
    report = {"matched": matched, "discarded": discarded}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    log.info(f"Alignment report written to {output_path}")

def main() -> None:
    """Entry point for the alignment script."""
    # Resolve raw data locations
    qm9_path = Path("data/raw/qm9.parquet")
    ir_path = Path("data/raw/ir_spectra.parquet")

    # Ensure raw files exist (download if missing)
    _ensure_raw_file(qm9_path, "lisn519010/QM9")
    _ensure_raw_file(ir_path, "lamblador/QM9-IR")

    log.info(f"Loading QM9 data from {qm9_path}")
    qm9_df = load_parquet(qm9_path)

    log.info(f"Loading IR spectra data from {ir_path}")
    ir_df = load_parquet(ir_path)

    log.info("Performing inner join on InChIKey")
    aligned_df = align_datasets(qm9_df, ir_df, key="InChIKey")

    matched = len(aligned_df)
    # Discarded = total rows in QM9 that did not find a match (as per original spec)
    discarded = len(qm9_df) - matched

    log.info(f"Alignment complete: matched={matched}, discarded={discarded}")

    # Write JSON report
    report_path = paths.data("processed", "alignment_report.json")
    write_report(matched, discarded, report_path)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.error(f"Alignment failed: {e}", exc_info=True)
        raise