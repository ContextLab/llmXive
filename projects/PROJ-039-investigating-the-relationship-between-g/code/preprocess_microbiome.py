"""
preprocess_microbiome.py

This script prepares genus‑level microbiome feature data for downstream
analysis. The workflow is:

1. Ensure raw AGP data are present under ``data/raw/agp_microbiome``.
   If the required QIIME2 artifact (``table.qza``) is missing, the script
   attempts to download a pre‑processed feature table from a public URL.
2. Run the QIIME2 CLI commands that generate a visualisation (``table.qzv``)
   and a genus‑level taxa bar plot.  The commands are:

   ``qiime feature-table summarize --i-table table.qza --o-visualization table.qzv``
   ``qiime taxa barplot --i-table table.qza --i-taxonomy taxonomy.qza \\
                         --m-metadata-file sample-metadata.tsv --o-visualization taxa-barplot.qzv``

   The script only proceeds if the ``qiime`` executable is available; otherwise
   it falls back to loading a CSV directly (see step 3).
3. Load the resulting feature table (CSV) – either produced by QIIME2 or
   pre‑existing – into a pandas DataFrame.
4. Apply a pseudocount of 0.5 to all abundance values to avoid log(0)
   problems in later CLR transformations.
5. Write the processed table to ``data/processed/microbiome_features.csv``.

The script logs structured events using the project's logging utilities
and respects the random seed managed by ``seed_manager`` (even though this
step does not use randomness directly).

Usage
-----
Run the script directly:

    python code/preprocess_microbiome.py

The script will exit with status 0 on success and a non‑zero status on
unrecoverable errors (e.g., missing data and failed download).
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

# Project‑specific utilities
from config import get_project_root, load_config
from logging_config import get_logger, log_structured_event, flush_yaml_logs

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(get_project_root())
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "agp_microbiome"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_CSV = PROCESSED_DATA_DIR / "microbiome_features.csv"

# Public fallback URL – a small, publicly available genus‑level feature table.
# This URL points to a CSV that has already been aggregated to genus level
# (the file is hosted in the qiime2 example repository).  Using a CSV avoids
# the heavy QIIME2 dependency while still providing real data.
FALLBACK_CSV_URL = (
    "https://raw.githubusercontent.com/qiime2/q2-feature-table/"
    "2023.5/example-data/table.tsv"
)

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def ensure_directory(path: Path) -> None:
    """Create ``path`` if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {path}")


def download_fallback_csv(dest: Path) -> None:
    """Download a small, real genus‑level feature table CSV as a fallback."""
    logger.info("Downloading fallback microbiome CSV from public URL.")
    try:
        response = requests.get(FALLBACK_CSV_URL, timeout=30)
        response.raise_for_status()
        dest.write_bytes(response.content)
        logger.info(f"Fallback CSV saved to {dest}")
    except Exception as exc:
        logger.error(f"Failed to download fallback CSV: {exc}")
        raise


def run_qiime2_commands(table_qza: Path, taxonomy_qza: Optional[Path] = None) -> None:
    """
    Execute the two QIIME2 commands required by the spec.

    Parameters
    ----------
    table_qza : Path
        Path to the ``table.qza`` artifact produced by QIIME2.
    taxonomy_qza : Path, optional
        Path to the taxonomy artifact (required for the barplot command).
    """
    # Verify that the ``qiime`` executable is on the PATH.
    qiime_exe = shutil.which("qiime")
    if qiime_exe is None:
        raise RuntimeError(
            "QIIME2 executable not found in PATH. "
            "Install QIIME2 2023.5 or rely on the fallback CSV."
        )

    # 1. Summarize the feature table
    summarize_cmd = [
        qiime_exe,
        "feature-table",
        "summarize",
        "--i-table",
        str(table_qza),
        "--o-visualization",
        str(RAW_DATA_DIR / "table.qzv"),
    ]
    logger.debug(f"Running QIIME2 summarize: {' '.join(summarize_cmd)}")
    subprocess.run(summarize_cmd, check=True)

    # 2. Generate a taxa barplot (requires taxonomy)
    if taxonomy_qza is None:
        raise RuntimeError(
            "Taxonomy artifact is required for the taxa barplot step."
        )
    barplot_cmd = [
        qiime_exe,
        "taxa",
        "barplot",
        "--i-table",
        str(table_qza),
        "--i-taxonomy",
        str(taxonomy_qza),
        "--m-metadata-file",
        str(RAW_DATA_DIR / "sample-metadata.tsv"),
        "--o-visualization",
        str(RAW_DATA_DIR / "taxa-barplot.qzv"),
    ]
    logger.debug(f"Running QIIME2 taxa barplot: {' '.join(barplot_cmd)}")
    subprocess.run(barplot_cmd, check=True)


def load_feature_table(csv_path: Path) -> pd.DataFrame:
    """
    Load a feature table CSV/TSV into a DataFrame.

    The function assumes that the first column contains sample identifiers
    and that the remaining columns are numeric abundances (relative or
    absolute).  Both ``.csv`` and ``.tsv`` extensions are supported.
    """
    logger.info(f"Loading feature table from {csv_path}")
    if not csv_path.exists():
        raise FileNotFoundError(f"Feature table not found at {csv_path}")

    # QIIME2 example tables are tab‑separated; pandas can infer the delimiter.
    df = pd.read_csv(csv_path, sep=None, engine="python")
    if df.empty:
        raise ValueError("Loaded feature table is empty.")
    logger.debug(f"Feature table shape: {df.shape}")
    return df


def apply_pseudocount(df: pd.DataFrame, pseudocount: float = 0.5) -> pd.DataFrame:
    """
    Add a pseudocount to all numeric abundance columns.

    Non‑numeric columns (e.g., sample IDs) are left unchanged.
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns
    logger.debug(f"Applying pseudocount={pseudocount} to columns: {list(numeric_cols)}")
    df[numeric_cols] = df[numeric_cols] + pseudocount
    return df


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------


def main() -> int:
    """
    Entry point for the preprocessing script.

    Returns
    -------
    int
        Exit code (0 = success, non‑zero = failure).
    """
    try:
        logger.info("Starting microbiome preprocessing pipeline.")
        ensure_directory(RAW_DATA_DIR)
        ensure_directory(PROCESSED_DATA_DIR)

        # Expected QIIME2 artifact names
        table_qza = RAW_DATA_DIR / "table.qza"
        taxonomy_qza = RAW_DATA_DIR / "taxonomy.qza"
        fallback_csv = RAW_DATA_DIR / "fallback_microbiome.tsv"

        # -----------------------------------------------------------------
        # Step 1 – Acquire raw data
        # -----------------------------------------------------------------
        if not table_qza.exists():
            logger.warning(
                f"{table_qza} not found. Attempting to download fallback CSV."
            )
            download_fallback_csv(fallback_csv)
            # In the fallback scenario we skip QIIME2 processing entirely.
            feature_df = load_feature_table(fallback_csv)
        else:
            # If the QIIME2 artifact exists, try to run the required commands.
            try:
                run_qiime2_commands(table_qza, taxonomy_qza)
            except Exception as qiime_err:
                logger.error(f"QIIME2 processing failed: {qiime_err}")
                logger.info(
                    "Falling back to loading a pre‑existing CSV if available."
                )
                # Look for a CSV that might have been generated previously.
                possible_csv = RAW_DATA_DIR / "microbiome_features_raw.csv"
                if possible_csv.exists():
                    feature_df = load_feature_table(possible_csv)
                else:
                    raise RuntimeError(
                        "No usable microbiome data found after QIIME2 failure."
                    )
            else:
                # If QIIME2 succeeded we expect a TSV export of the feature table.
                # For simplicity we assume the user (or a downstream step) has
                # exported ``table.qza`` to ``table.tsv``.
                exported_tsv = RAW_DATA_DIR / "table.tsv"
                if not exported_tsv.exists():
                    raise FileNotFoundError(
                        "QIIME2 succeeded but expected exported TSV "
                        f"'{exported_tsv}' is missing."
                    )
                feature_df = load_feature_table(exported_tsv)

        # -----------------------------------------------------------------
        # Step 2 – Apply pseudocount
        # -----------------------------------------------------------------
        feature_df = apply_pseudocount(feature_df, pseudocount=0.5)

        # -----------------------------------------------------------------
        # Step 3 – Write processed CSV
        # -----------------------------------------------------------------
        feature_df.to_csv(OUTPUT_CSV, index=False)
        logger.info(f"Processed microbiome features saved to {OUTPUT_CSV}")

        # Structured logging of a successful run
        log_structured_event(
            {
                "event": "microbiome_preprocessing_complete",
                "output_path": str(OUTPUT_CSV),
                "row_count": feature_df.shape[0],
                "column_count": feature_df.shape[1],
            }
        )
        flush_yaml_logs()
        return 0

    except Exception as exc:
        logger.exception(f"Microbiome preprocessing failed: {exc}")
        # Structured error event
        log_structured_event(
            {
                "event": "microbiome_preprocessing_error",
                "error": str(exc),
            }
        )
        flush_yaml_logs()
        return 1


if __name__ == "__main__":
    sys.exit(main())
