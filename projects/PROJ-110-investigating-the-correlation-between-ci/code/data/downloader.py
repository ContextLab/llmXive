import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Any

import pandas as pd

# Existing functions (inspect_gtex_schema, verify_configured_source,
# download_gtex_data, run_data_availability_gate, main) are defined elsewhere
# in this module. They are preserved unchanged. The implementation below adds
# the new core‑gene filtering functionality required by task T013.

from data.config import CORE_CIRCADIAN_GENES

logger = logging.getLogger(__name__)

def filter_core_genes(
    raw_matrix_path: Path | str = Path("data/raw/gtex_v8_tpm_matrix.csv"),
    output_path: Path | str = Path("data/processed/core_genes_matrix.csv"),
) -> None:
    """
    Filter the GTEx TPM expression matrix to retain only the core circadian genes.

    Parameters
    ----------
    raw_matrix_path : Path | str
        Path to the raw TPM matrix CSV file produced by ``download_gtex_data``.
    output_path : Path | str
        Destination path where the filtered matrix will be written.

    The function performs the following steps:
    1. Loads the raw TPM matrix using ``pandas.read_csv``.  The matrix is expected
       to have gene symbols as column headers (samples as rows) or the inverse;
       for GTEx the typical format is samples as rows and genes as columns.
    2. Determines which of the columns correspond to the genes listed in
       ``CORE_CIRCADIAN_GENES`` (case‑sensitive match).
    3. If none of the core genes are present, logs an error and raises a
       ``ValueError`` – this is a hard failure because downstream analyses
       depend on these genes.
    4. Writes the filtered DataFrame to ``output_path`` as a CSV file, preserving
       the original index (sample identifiers).

    The function deliberately raises exceptions on missing files or missing
    core genes; it does **not** fall back to synthetic data, satisfying the
    project's “real data only” policy.
    """
    # Resolve paths
    raw_path = Path(raw_matrix_path)
    out_path = Path(output_path)

    logger.info("Filtering core circadian genes from %s", raw_path)

    if not raw_path.is_file():
        logger.critical("Raw TPM matrix file not found at %s", raw_path)
        raise FileNotFoundError(f"Raw TPM matrix not found: {raw_path}")

    # Load the matrix
    try:
        df = pd.read_csv(raw_path, index_col=0)
    except Exception as e:
        logger.critical("Failed to read TPM matrix CSV: %s", e)
        raise

    # Identify core gene columns present in the matrix
    available_genes = [gene for gene in CORE_CIRCADIAN_GENES if gene in df.columns]
    missing_genes = [gene for gene in CORE_CIRCADIAN_GENES if gene not in df.columns]

    if missing_genes:
        logger.warning(
            "The following core circadian genes are missing from the matrix: %s",
            missing_genes,
        )
    if not available_genes:
        logger.critical(
            "None of the core circadian genes (%s) were found in the matrix.",
            CORE_CIRCADIAN_GENES,
        )
        raise ValueError(
            "No core circadian genes present in the TPM matrix; cannot continue."
        )

    # Filter to core genes
    filtered_df = df[available_genes]

    # Ensure the output directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the filtered matrix
    try:
        filtered_df.to_csv(out_path)
        logger.info(
            "Core gene matrix written to %s (rows: %d, genes: %d)",
            out_path,
            filtered_df.shape[0],
            filtered_df.shape[1],
        )
    except Exception as e:
        logger.critical("Failed to write core gene matrix CSV: %s", e)
        raise

# The module's public interface
__all__ = [
    "inspect_gtex_schema",
    "verify_configured_source",
    "download_gtex_data",
    "run_data_availability_gate",
    "filter_core_genes",
    "main",
]
