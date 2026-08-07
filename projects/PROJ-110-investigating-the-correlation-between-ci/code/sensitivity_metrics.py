"""
Utility functions for sensitivity analysis metrics.
"""

import pandas as pd
from pathlib import Path
from typing import Union

def calculate_agreement_rate(sensitivity_csv_path: Union[str, Path]) -> float:
    """
    Calculate the classification agreement rate between baseline and varied labels.

    Parameters
    ----------
    sensitivity_csv_path : Union[str, Path]
        Path to the CSV file produced by ``run_sensitivity_analysis``. The file
        must contain the columns ``baseline_label`` and ``varied_label``.

    Returns
    -------
    float
        Proportion of samples where the baseline label matches the varied label.
        Returns ``0.0`` for an empty file.
    """
    path = Path(sensitivity_csv_path)
    df = pd.read_csv(path)

    total = len(df)
    if total == 0:
        return 0.0

    agreement = (df["baseline_label"] == df["varied_label"]).sum()
    return agreement / total
