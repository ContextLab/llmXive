"""Data preprocessing utilities.

Currently provides a log‑transformation step for the core circadian gene
expression matrix (TPM → log2(TPM + 1)).
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def log_transform_expression(
    input_path: Path = Path("data/processed/core_genes_matrix.csv"),
    output_path: Path = Path("data/processed/core_genes_log2_matrix.csv"),
) -> None:
    """Add a pseudocount of 1 to TPM values and compute log2(TPM + 1).

    Parameters
    ----------
    input_path: Path
        Path to the CSV file produced by ``filter_core_genes`` containing raw
        TPM values for the core circadian genes. The first column is expected
        to be a sample identifier; all subsequent columns are numeric TPMs.
    output_path: Path
        Destination path for the log‑transformed matrix. The directory hierarchy
        will be created if it does not already exist.
    """
    logger.info("Loading core genes matrix from %s", input_path)
    df = pd.read_csv(input_path)

    # Identify the sample identifier column (assumed to be the first column)
    sample_id_col = df.columns[0]
    numeric_cols = df.columns[1:]

    logger.debug(
        "Applying log2 transformation with pseudocount to %d numeric columns",
        len(numeric_cols),
    )
    df[numeric_cols] = np.log2(df[numeric_cols] + 1)

    logger.info("Writing log‑transformed matrix to %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)