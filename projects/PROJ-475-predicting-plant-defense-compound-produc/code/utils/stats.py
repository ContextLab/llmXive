"""
Statistics Utilities Module.

This module provides statistical functions including:
- VIF calculation
- Jaccard index calculations
- Benjamini-Hochberg correction
"""

import logging
import sys
from pathlib import Path
from typing import List, Set, Dict, Any, Union, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logger.warning("statsmodels not installed. VIF calculations will not work.")


def calculate_vif(df: pd.DataFrame, feature_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.

    Args:
        df: DataFrame containing features.
        feature_cols: List of feature column names. If None, all numeric columns are used.

    Returns:
        pd.DataFrame: DataFrame with feature names and their VIF values.

    Raises:
        ImportError: If statsmodels is not installed.
    """
    if not HAS_STATSMODELS:
        raise ImportError("statsmodels is required for VIF calculation. Install with: pip install statsmodels")

    if feature_cols is None:
        exclude_cols = ["population_id", "compound_id", "env_id", "target", "compound_concentration", "defense_score"]
        feature_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col not in exclude_cols]

    if len(feature_cols) < 2:
        return pd.DataFrame(columns=["feature", "vif"])

    # Remove columns with zero variance
    feature_cols = [col for col in feature_cols if df[col].std() > 0]

    if len(feature_cols) < 2:
        return pd.DataFrame(columns=["feature", "vif"])

    vif_results = []
    X = df[feature_cols].copy()
    X = sm.add_constant(X)

    for i, feature in enumerate(feature_cols):
        try:
            vif = variance_inflation_factor(X.values, i + 1)
            vif_results.append({"feature": feature, "vif": vif})
        except Exception as e:
            logger.error(f"Error calculating VIF for '{feature}': {e}")
            vif_results.append({"feature": feature, "vif": np.nan})

    return pd.DataFrame(vif_results).sort_values("vif", ascending=False)


def run_vif_analysis(df: pd.DataFrame, threshold: float = 5.0) -> Tuple[pd.DataFrame, List[str]]:
    """
    Run VIF analysis and identify features to remove.

    Args:
        df: Input DataFrame.
        threshold: VIF threshold for flagging (default 5.0).

    Returns:
        Tuple[pd.DataFrame, List[str]]: (VIF results, list of features to remove)
    """
    vif_df = calculate_vif(df)
    high_vif_features = vif_df[vif_df["vif"] > threshold]["feature"].tolist()
    return vif_df, high_vif_features


def calculate_jaccard_index(set1: Set[Any], set2: Set[Any]) -> float:
    """
    Calculate Jaccard index between two sets.

    Args:
        set1: First set.
        set2: Second set.

    Returns:
        float: Jaccard index (0 to 1).
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))

    return intersection / union if union > 0 else 0.0


def calculate_jaccard_stability_matrix(feature_sets: List[Set[Any]]) -> pd.DataFrame:
    """
    Calculate Jaccard stability matrix for multiple feature sets.

    Args:
        feature_sets: List of feature sets (e.g., from different alpha values).

    Returns:
        pd.DataFrame: Symmetric matrix of Jaccard indices.
    """
    n = len(feature_sets)
    if n == 0:
        return pd.DataFrame()

    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            matrix[i, j] = calculate_jaccard_index(feature_sets[i], feature_sets[j])

    return pd.DataFrame(matrix, index=range(n), columns=range(n))


def calculate_mean_jaccard_stability(feature_sets: List[Set[Any]]) -> float:
    """
    Calculate mean Jaccard stability across all pairs.

    Args:
        feature_sets: List of feature sets.

    Returns:
        float: Mean Jaccard index (excluding diagonal).
    """
    if len(feature_sets) < 2:
        return 1.0

    matrix = calculate_jaccard_stability_matrix(feature_sets)
    n = len(matrix)

    # Exclude diagonal
    off_diagonal = matrix.values[np.triu_indices(n, k=1)]
    return np.mean(off_diagonal) if len(off_diagonal) > 0 else 0.0


def save_jaccard_stability_report(feature_sets: List[Set[Any]], output_path: Union[str, Path]):
    """
    Save Jaccard stability report to a file.

    Args:
        feature_sets: List of feature sets.
        output_path: Path to save the report.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    matrix = calculate_jaccard_stability_matrix(feature_sets)
    mean_stability = calculate_mean_jaccard_stability(feature_sets)

    with open(output_path, "w") as f:
        f.write("Jaccard Stability Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Mean Stability: {mean_stability:.4f}\n\n")
        f.write("Stability Matrix:\n")
        f.write(matrix.to_string())

    logger.info(f"Saved Jaccard stability report to {output_path}")


def benjamini_hochberg_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.

    Args:
        p_values: List of p-values.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple[List[bool], List[float]]: (significant flags, adjusted p-values)
    """
    n = len(p_values)
    if n == 0:
        return [], []

    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]

    # Calculate adjusted p-values
    adjusted_p_values = [0.0] * n
    for i, p in enumerate(sorted_p_values):
        rank = i + 1
        adjusted_p = p * n / rank
        adjusted_p_values[sorted_indices[i]] = min(adjusted_p, 1.0)

    # Ensure monotonicity (adjusted p-values should not decrease)
    for i in range(n - 2, -1, -1):
        adjusted_p_values[sorted_indices[i]] = min(
            adjusted_p_values[sorted_indices[i]],
            adjusted_p_values[sorted_indices[i + 1]]
        )

    # Determine significance
    significant = [p <= alpha for p in adjusted_p_values]

    return significant, adjusted_p_values


def apply_bh_correction_to_predictors(predictor_p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg correction to predictor p-values.

    Args:
        predictor_p_values: Dictionary mapping predictor names to p-values.
        alpha: Significance level.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary with corrected results.
    """
    predictors = list(predictor_p_values.keys())
    p_values = list(predictor_p_values.values())

    significant, adjusted_p_values = benjamini_hochberg_correction(p_values, alpha)

    result = {}
    for i, predictor in enumerate(predictors):
        result[predictor] = {
            "original_p_value": predictor_p_values[predictor],
            "adjusted_p_value": adjusted_p_values[i],
            "significant": significant[i]
        }

    return result


def main():
    """Main entry point for stats module."""
    # Example usage
    logger.info("Stats module loaded successfully")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())