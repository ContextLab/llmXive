import pandas as pd
import numpy as np


def run_benjamini_hochberg(
    pvals_df: pd.DataFrame,
    alpha: float = 0.05,
    pcol: str = "p_value",
    adj_pcol: str = "p_adj",
    signif_col: str = "significant",
) -> pd.DataFrame:
    """
    Apply Benjamini‑Hochberg FDR correction to a DataFrame of p‑values.

    Parameters
    ----------
    pvals_df : pd.DataFrame
        DataFrame that contains a column with raw p‑values.
    alpha : float, optional
        Desired false discovery rate (default 0.05).
    pcol : str, optional
        Name of the column containing the raw p‑values.
    adj_pcol : str, optional
        Name of the column to store the adjusted p‑values.
    signif_col : str, optional
        Name of the boolean column indicating significance after correction.

    Returns
    -------
    pd.DataFrame
        A copy of ``pvals_df`` with two new columns: ``adj_pcol`` and ``signif_col``.
    """
    if pcol not in pvals_df.columns:
        raise ValueError(f"Column '{pcol}' not found in input DataFrame.")

    # Work on a copy to avoid side‑effects
    df = pvals_df.copy().reset_index(drop=True)

    # Number of hypotheses
    m = df.shape[0]
    if m == 0:
        # Nothing to correct
        df[adj_pcol] = np.nan
        df[signif_col] = False
        return df

    # Sort by p‑value (ascending)
    order = df[pcol].argsort()
    sorted_p = df.loc[order, pcol].values

    # Compute BH adjusted p‑values
    ranks = np.arange(1, m + 1)
    bh_values = sorted_p * m / ranks

    # Ensure monotonicity (non‑increasing when moving from smallest to largest p)
    bh_adj = np.minimum.accumulate(bh_values[::-1])[::-1]

    # Clip to [0, 1]
    bh_adj = np.clip(bh_adj, 0, 1)

    # Place adjusted values back to original order
    adj_series = pd.Series(bh_adj, index=order).reindex(df.index)
    df[adj_pcol] = adj_series.values
    df[signif_col] = df[adj_pcol] <= alpha
    return df