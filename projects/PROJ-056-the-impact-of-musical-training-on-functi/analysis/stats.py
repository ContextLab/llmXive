"""
Very small placeholder for statistical analysis.

Returns an empty DataFrame with the columns required by downstream
output modules.
"""

import pandas as pd

def process_connectivity_statistics(matrices):
    """
    Placeholder – in synthetic verification we do not perform real tests.

    Parameters
    ----------
    matrices : np.ndarray
        3‑D array of connectivity matrices (subjects × ROIs × ROIs).

    Returns
    -------
    pd.DataFrame
        Empty DataFrame with the expected schema.
    """
    cols = [
        "connection_id",
        "t_stat",
        "p_value",
        "q_value",
        "effect_size",
        "ci_lower",
        "ci_upper",
    ]
    return pd.DataFrame(columns=cols)
