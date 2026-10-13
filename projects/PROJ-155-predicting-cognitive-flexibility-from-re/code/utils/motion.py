"""
Motion artifact handling.
"""

import numpy as np
import pandas as pd


def calculate_mean_fd(motion_params: np.ndarray) -> float:
    if motion_params.ndim != 2 or motion_params.shape[1] != 6:
        raise ValueError("Expected (n_timepoints, 6)")
    diffs = np.diff(motion_params, axis=0)
    # Convert rotations (radians) to mm (approx 50mm radius)
    diffs[:, 3:6] *= 50.0
    fd = np.sum(np.abs(diffs), axis=1)
    return float(np.mean(fd))

def filter_by_motion(df: pd.DataFrame, threshold: float = 0.2) -> tuple[pd.DataFrame, list[str]]:
    if "Mean_FD" not in df.columns:
        return df, []
    excluded = df[df["Mean_FD"] > threshold]["Subject_ID"].tolist()
    filtered = df[df["Mean_FD"] <= threshold].reset_index(drop=True)
    return filtered, excluded
