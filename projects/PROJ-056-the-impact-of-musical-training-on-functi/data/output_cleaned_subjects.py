"""
Utility to write the cleaned subjects CSV required by later stages.
"""

import pandas as pd
from pathlib import Path

def write_cleaned_subjects(df: pd.DataFrame, path: Path):
    """
    Write the cleaned subject table to CSV.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned subject metadata.
    path : Path
        Destination CSV file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
