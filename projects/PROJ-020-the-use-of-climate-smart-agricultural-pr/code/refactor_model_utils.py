"""
Refactored model utilities to consolidate and standardize model-related functions.

This module consolidates functions from analysis.model, analysis.diagnostics,
and analysis.refactor_model into a unified interface for better maintainability.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor

logger = logging.getLogger(__name__)


def calculate_vif(df: pd.DataFrame, exclude_intercept: bool = True) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for all numeric columns.

    Args:
        df: DataFrame with numeric columns.
        exclude_intercept: If True, exclude the intercept column from calculation.

    Returns:
        Dictionary mapping column names to VIF values.
    """
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])

    if numeric_df.empty:
        logger.warning("No numeric columns found for VIF calculation")
        return {}

    # Add constant for intercept if needed
    if exclude_intercept:
        X = numeric_df
    else:
        X = sm.add_constant(numeric_df)

    vif_data = {}
    for i, col in enumerate(X.columns):
        try:
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for column {col}: {e}")
            vif_data[col] = np.nan

    return vif_data


def flag_collinearity(vif_dict: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Flag predictors with VIF above the threshold.

    Args:
        vif_dict: Dictionary of VIF values.
        threshold: VIF threshold for flagging (default 5.0).

    Returns:
        List of column names with high collinearity.
    """
    flagged = [col for col, vif in vif_dict.items() if not np.isnan(vif) and vif > threshold]
    if flagged:
        logger.warning(f"High collinearity detected for: {', '.join(flagged)} (VIF > {threshold})")
    return flagged


def get_collinearity_report(df: pd.DataFrame, threshold: float = 5.0) -> Dict[str, Any]:
    """
    Generate a comprehensive collinearity report.

    Args:
        df: DataFrame to analyze.
        threshold: VIF threshold for flagging.

    Returns:
        Dictionary containing VIF values, flagged columns, and summary statistics.
    """
    vif_dict = calculate_vif(df)
    flagged = flag_collinearity(vif_dict, threshold)

    return {
        "vif_values": vif_dict,
        "flagged_columns": flagged,
        "threshold": threshold,
        "max_vif": max((v for v in vif_dict.values() if not np.isnan(v)), default=0),
        "mean_vif": np.mean([v for v in vif_dict.values() if not np.isnan(v)]) if vif_dict else 0,
    }


def create_interaction_formula(
    base_predictors: List[str],
    interaction_terms: List[Tuple[str, str]],
    outcome: str,
    include_main_effects: bool = True
) -> str:
    """
    Create a formula string with interaction terms.

    Args:
        base_predictors: List of main predictor variables.
        interaction_terms: List of tuples representing interaction pairs.
        outcome: Name of the outcome variable.
        include_main_effects: If True, include main effects for interaction terms.

    Returns:
        Formula string suitable for statsmodels.
    """
    parts = [f"{outcome} ~"]

    # Add main effects
    if include_main_effects:
        parts.extend(base_predictors)
        for term1, term2 in interaction_terms:
            if term1 not in base_predictors:
                parts.append(term1)
            if term2 not in base_predictors:
                parts.append(term2)

    # Add interactions
    for term1, term2 in interaction_terms:
        parts.append(f"{term1}:{term2}")

    return " + ".join(parts)


def sanitize_formula_string(formula: str) -> str:
    """
    Sanitize a formula string by removing invalid characters.

    Args:
        formula: Raw formula string.

    Returns:
        Sanitized formula string.
    """
    import re

    # Remove any characters that aren't alphanumeric, spaces, or formula operators
    sanitized = re.sub(r"[^a-zA-Z0-9_+\-*:().\s]", "", formula)
    # Normalize whitespace
    sanitized = " ".join(sanitized.split())
    return sanitized


def check_formula_validity(formula: str, df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Check if a formula is valid for the given DataFrame.

    Args:
        formula: Formula string to validate.
        df: DataFrame to check against.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        # Parse formula to extract variable names
        parts = formula.replace("~", " ").replace("+", " ").replace("*", " ").replace(":", " ").split()
        variables = [p for p in parts if p not in ["~", "+", "*", ":", "1", "0"]]

        # Check if all variables exist in DataFrame
        missing = [v for v in variables if v not in df.columns]
        if missing:
            return False, f"Missing columns in DataFrame: {', '.join(missing)}"

        return True, ""
    except Exception as e:
        return False, f"Formula validation error: {e}"


def extract_predictor_names(formula: str) -> List[str]:
    """
    Extract predictor variable names from a formula string.

    Args:
        formula: Formula string.

    Returns:
        List of predictor variable names.
    """
    import re

    # Split by formula operators
    parts = re.split(r"[~+\*:]", formula)
    # Remove outcome variable (first part) and clean up
    predictors = []
    for part in parts[1:]:  # Skip outcome
        for var in part.split():
            if var and var not in ["1", "0", "C(", ")"]:
                # Handle C() notation
                clean_var = re.sub(r"C\(([^)]+)\)", r"\1", var)
                predictors.append(clean_var)

    return list(set(predictors))


def format_model_summary(model_result: Any) -> Dict[str, Any]:
    """
    Format model summary into a structured dictionary.

    Args:
        model_result: Result from a statsmodels model fit.

    Returns:
        Dictionary with formatted model results.
    """
    summary = {}

    try:
        # Extract coefficients
        if hasattr(model_result, "params"):
            summary["coefficients"] = model_result.params.to_dict()

        if hasattr(model_result, "pvalues"):
            summary["p_values"] = model_result.pvalues.to_dict()

        if hasattr(model_result, "conf_int"):
            conf_int = model_result.conf_int()
            summary["confidence_intervals"] = {
                col: {"lower": row[0], "upper": row[1]}
                for col, row in conf_int.iterrows()
            }

        if hasattr(model_result, "rsquared"):
            summary["r_squared"] = model_result.rsquared

        if hasattr(model_result, "rsquared_adj"):
            summary["adjusted_r_squared"] = model_result.rsquared_adj

        if hasattr(model_result, "f_pvalue"):
            summary["f_pvalue"] = model_result.f_pvalue

        if hasattr(model_result, "bse"):
            summary["standard_errors"] = model_result.bse.to_dict()

    except Exception as e:
        logger.error(f"Error formatting model summary: {e}")
        summary["error"] = str(e)

    return summary


def safe_model_fit(
    formula: str,
    df: pd.DataFrame,
    use_categorical: bool = True,
    **kwargs
) -> Optional[Any]:
    """
    Safely fit a model with error handling.

    Args:
        formula: Model formula string.
        df: DataFrame containing the data.
        use_categorical: Automatically convert object columns to categorical.
        **kwargs: Additional arguments passed to the model fit method.

    Returns:
        Fitted model result or None if fitting failed.
    """
    try:
        # Prepare data
        data = df.copy()

        # Convert categorical variables if requested
        if use_categorical:
            for col in data.columns:
                if data[col].dtype == "object":
                    data[col] = data[col].astype("category")

        # Validate formula
        is_valid, error_msg = check_formula_validity(formula, data)
        if not is_valid:
            logger.error(f"Invalid formula: {error_msg}")
            return None

        # Fit model
        model = smf.ols(formula, data=data)
        result = model.fit(**kwargs)

        return result

    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return None


def calculate_fdr_adjusted_pvalues(pvalues: List[float]) -> List[float]:
    """
    Calculate Benjamini-Hochberg FDR adjusted p-values.

    Args:
        pvalues: List of raw p-values.

    Returns:
        List of adjusted p-values.
    """
    import numpy as np

    pvalues = np.array(pvalues)
    n = len(pvalues)
    if n == 0:
        return []

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = pvalues[sorted_indices]

    # Calculate adjusted p-values
    adjusted = np.zeros(n)
    for i, p in enumerate(sorted_pvalues):
        adjusted[sorted_indices[i]] = min(p * n / (i + 1), 1.0)

    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adjusted[sorted_indices[i]] = min(adjusted[sorted_indices[i]], adjusted[sorted_indices[i + 1]])

    return adjusted.tolist()


def run_mixed_effects_model(
    formula: str,
    df: pd.DataFrame,
    groups: Optional[List[str]] = None,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Run a mixed effects model with error handling.

    Args:
        formula: Model formula.
        df: Data DataFrame.
        groups: List of grouping variables (for random effects).
        **kwargs: Additional arguments for the model.

    Returns:
        Dictionary with model results or None if fitting failed.
    """
    try:
        # Prepare data
        data = df.copy()

        # For simple implementation, use OLS if groups not specified
        # In a full implementation, this would use statsmodels mixedlm
        if groups:
            logger.warning("Mixed effects not fully implemented; using OLS as fallback")

        result = safe_model_fit(formula, data, **kwargs)
        if result is None:
            return None

        return format_model_summary(result)

    except Exception as e:
        logger.error(f"Mixed effects model failed: {e}")
        return None


def main() -> None:
    """Main entry point for testing utilities."""
    logging.basicConfig(level=logging.INFO)

    # Create sample data for testing
    np.random.seed(42)
    n = 100
    sample_df = pd.DataFrame({
        "y": np.random.randn(n),
        "x1": np.random.randn(n),
        "x2": np.random.randn(n),
        "x3": np.random.randn(n),
        "category": np.random.choice(["A", "B", "C"], n),
    })

    # Test VIF calculation
    vif_results = calculate_vif(sample_df)
    logger.info(f"VIF Results: {vif_results}")

    # Test collinearity flagging
    flagged = flag_collinearity(vif_results)
    logger.info(f"Flagged columns: {flagged}")

    # Test formula creation
    formula = create_interaction_formula(
        base_predictors=["x1", "x2"],
        interaction_terms=[("x1", "x2")],
        outcome="y"
    )
    logger.info(f"Created formula: {formula}")

    # Test model fitting
    result = safe_model_fit(formula, sample_df)
    if result:
        summary = format_model_summary(result)
        logger.info(f"Model R-squared: {summary.get('r_squared', 'N/A')}")

    logger.info("Refactored model utilities test completed.")


if __name__ == "__main__":
    main()