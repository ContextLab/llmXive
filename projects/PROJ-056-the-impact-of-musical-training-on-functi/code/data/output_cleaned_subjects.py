"""
Helper that writes the cleaned subject table produced by the preprocessing
stage to ``subjects_cleaned.csv``. The function is deliberately tiny – it
only ensures the output directory exists and uses the project's logging
utilities.
"""

import pandas as pd
from pathlib import Path
from utils.logging import get_logger

log = get_logger(__name__)

def write_cleaned_subjects(df: pd.DataFrame, output_path: Path) -> None:
    """
    Persist the cleaned subject DataFrame to CSV.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame produced by ``preprocess_subjects``.
    output_path : Path
        Destination file (including filename). The parent directory will be
        created if it does not already exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info(f"Cleaned subjects written to {output_path}")
