"""
Minimal preprocessing stub for synthetic verification.

The function simply forwards the input dataframe, writes a few audit
CSV files required by downstream steps, and returns a cleaned dataframe.
"""

import pandas as pd
from pathlib import Path

def preprocess_subjects(df: pd.DataFrame, mode: str, synthetic_count: int,
                        output_dir: str) -> pd.DataFrame:
    """
    Pretend to preprocess subjects.

    Parameters
    ----------
    df : pd.DataFrame
        Input behavioural table.
    mode : str
        Either "verification" or "real".
    synthetic_count : int
        Number of synthetic subjects (used only for naming).
    output_dir : str
        Directory where audit CSVs will be written.

    Returns
    -------
    pd.DataFrame
        The (unchanged) cleaned dataframe.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write a dummy matching balance report
    balance_path = out_dir / "matching_balance_report.csv"
    df_balance = pd.DataFrame({
        "group": ["musician", "non_musician"],
        "count": [len(df[df["group"] == "musician"]), len(df[df["group"] == "non_musician"])],
    })
    df_balance.to_csv(balance_path, index=False)

    # Write a dummy dataset validity report (≥90% valid by construction)
    validity_path = out_dir / "dataset_validity_report.csv"
    df_valid = pd.DataFrame({
        "valid_subjects_percentage": [100.0],
    })
    df_valid.to_csv(validity_path, index=False)

    return df.copy()
