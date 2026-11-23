import numpy as np
import pandas as pd
from scipy.stats import shapiro, pearsonr, spearmanr
from typing import Tuple, List, Dict, Optional
import warnings
import os

def check_normality(data: pd.Series, alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality on a data series.

    Args:
        data: The data series to test.
        alpha: Significance level for the test.

    Returns:
        Tuple of (is_normal, p_value).
        is_normal is True if p_value > alpha (fail to reject null hypothesis).
    """
    if len(data) < 3:
        # Not enough data for Shapiro-Wilk, assume normality to proceed or flag
        warnings.warn("Less than 3 data points; skipping normality test.")
        return True, 1.0

    stat, p_value = shapiro(data.dropna())
    return p_value > alpha, p_value

def calculate_correlation(
    x: pd.Series, y: pd.Series, method: str = "pearson"
) -> Tuple[float, float]:
    """
    Calculate correlation coefficient and p-value between two series.

    Args:
        x: First data series.
        y: Second data series.
        method: 'pearson' or 'spearman'.

    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    # Drop pairs with missing values
    mask = ~(x.isna() | y.isna())
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 3:
        return np.nan, np.nan

    if method == "pearson":
        r, p = pearsonr(x_clean, y_clean)
    elif method == "spearman":
        r, p = spearmanr(x_clean, y_clean)
    else:
        raise ValueError(f"Unknown correlation method: {method}")

    return r, p

def benjamini_hochberg_fdr(p_values: List[float], q: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Args:
        p_values: List of raw p-values.
        q: False Discovery Rate threshold (default 0.05).

    Returns:
        List of booleans indicating if the corresponding p-value is significant
        after FDR correction.
    """
    if not p_values:
        return []

    n = len(p_values)
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]

    # Calculate adjusted p-values (q-values)
    # p_adj[i] = min( p[j] * n / (j+1) for j >= i )
    # We compute the threshold for significance directly:
    # Reject H_i if p_i <= (i+1)/n * q (for sorted p)
    # But to be precise with the step-up procedure, we calculate adjusted p-values.

    adjusted_p = [0.0] * n
    min_val = 1.0
    for i in range(n - 1, -1, -1):
        val = sorted_p[i] * n / (i + 1)
        if val < min_val:
            min_val = val
        else:
            val = min_val
        adjusted_p[sorted_indices[i]] = min(1.0, val)

    # Determine significance based on adjusted p-values
    significant = [p_adj < q for p_adj in adjusted_p]
    return significant

def run_correlation_analysis(
    structural_metrics: pd.DataFrame,
    dynamic_metrics: pd.DataFrame,
    alpha: float = 0.05,
    fdr_q: float = 0.05,
) -> pd.DataFrame:
    """
    Perform correlation analysis between structural and dynamic metrics.

    1. Check normality for each metric column.
    2. Select Pearson or Spearman based on normality.
    3. Compute correlations between all structural and dynamic metric pairs.
    4. Apply Benjamini-Hochberg FDR correction.

    Args:
        structural_metrics: DataFrame with structural metrics (index=subject_id).
        dynamic_metrics: DataFrame with dynamic metrics (index=subject_id).
        alpha: Significance level for normality test.
        fdr_q: FDR threshold.

    Returns:
        DataFrame with columns: metric_structural, metric_dynamic, r_value, p_value, is_significant_fdr.
    """
    # Ensure alignment
    common_subjects = structural_metrics.index.intersection(dynamic_metrics.index)
    if len(common_subjects) == 0:
        raise ValueError("No common subjects between structural and dynamic metrics.")

    struct_aligned = structural_metrics.loc[common_subjects]
    dyn_aligned = dynamic_metrics.loc[common_subjects]

    results = []
    p_values_list = []

    # Determine correlation method for each metric
    struct_methods = {}
    dyn_methods = {}

    for col in struct_aligned.columns:
        is_normal, _ = check_normality(struct_aligned[col], alpha)
        struct_methods[col] = "pearson" if is_normal else "spearman"

    for col in dyn_aligned.columns:
        is_normal, _ = check_normality(dyn_aligned[col], alpha)
        dyn_methods[col] = "pearson" if is_normal else "spearman"

    # Compute correlations
    for s_col in struct_aligned.columns:
        for d_col in dyn_aligned.columns:
            method = "pearson" if (struct_methods[s_col] == "pearson" and dyn_methods[d_col] == "pearson") else "spearman"
            r, p = calculate_correlation(struct_aligned[s_col], dyn_aligned[d_col], method)
            results.append({
                "metric_structural": s_col,
                "metric_dynamic": d_col,
                "r_value": r,
                "p_value": p,
                "method": method
            })
            p_values_list.append(p)

    df_results = pd.DataFrame(results)

    # Apply FDR correction
    if df_results.empty:
        df_results["is_significant_fdr"] = False
        df_results["p_value_fdr_corrected"] = np.nan
    else:
        # We need adjusted p-values for the report, not just boolean
        # Re-implement adjusted p-value calculation for the full list
        n = len(p_values_list)
        sorted_indices = sorted(range(n), key=lambda i: p_values_list[i])
        sorted_p = [p_values_list[i] for i in sorted_indices]

        adjusted_p = [0.0] * n
        min_val = 1.0
        for i in range(n - 1, -1, -1):
            val = sorted_p[i] * n / (i + 1)
            if val < min_val:
                min_val = val
            else:
                val = min_val
            adjusted_p[sorted_indices[i]] = min(1.0, val)

        df_results["p_value_fdr_corrected"] = adjusted_p
        df_results["is_significant_fdr"] = [p_adj < fdr_q for p_adj in adjusted_p]

    return df_results

def main():
    """
    Entry point for correlation analysis.
    Reads processed metrics, runs analysis, saves results.
    """
    # Paths relative to project root
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data" / "processed"

    structural_path = data_dir / "structural_metrics.csv"
    dynamic_path = data_dir / "dynamic_metrics.csv"
    output_path = data_dir / "correlation_results.csv"

    if not structural_path.exists():
        raise FileNotFoundError(f"Structural metrics not found: {structural_path}")
    if not dynamic_path.exists():
        raise FileNotFoundError(f"Dynamic metrics not found: {dynamic_path}")

    # Load data
    # Expecting index to be subject_id
    struct_df = pd.read_csv(structural_path, index_col=0)
    dyn_df = pd.read_csv(dynamic_path, index_col=0)

    # Run analysis
    results_df = run_correlation_analysis(struct_df, dyn_df)

    # Save results
    results_df.to_csv(output_path, index=False)
    print(f"Correlation results saved to {output_path}")
    print(f"Significant findings (FDR q<0.05): {results_df['is_significant_fdr'].sum()}")

if __name__ == "__main__":
    main()