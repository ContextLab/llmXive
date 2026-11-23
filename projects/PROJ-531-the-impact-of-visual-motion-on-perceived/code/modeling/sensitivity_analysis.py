"""
T023: Sensitivity Analysis Implementation.

Performs a bootstrap-based sensitivity analysis on OLS model coefficients.
It sweeps decision thresholds and calculates the significance rate for each.

Input:
    data/results/model_metrics.json (from T021/T026)
    data/processed/raw_cleaned.csv (from T017)

Output:
    data/results/sensitivity_analysis.csv
"""
import os
import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
from pathlib import Path
from typing import Dict, Any, List

# Import logging utility if available, otherwise fallback to basic
try:
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

def load_model_metrics(metrics_path: Path) -> Dict[str, Any]:
    """Load the model metrics JSON file."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Model metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_cleaned_data(data_path: Path) -> pd.DataFrame:
    """Load the cleaned dataset."""
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    return pd.read_csv(data_path)

def run_bootstrap_sensitivity(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    n_bootstrap: int = 1000,
    threshold: float = 0.05
) -> Dict[str, float]:
    """
    Perform bootstrap resampling to calculate significance rates.

    For each threshold, we calculate the fraction of bootstrap samples
    where the p-value of the coefficient is < 0.05.

    Args:
        df: The cleaned dataframe.
        target_col: Name of the target variable (agency_score).
        feature_cols: List of feature names (latency, smoothness, etc.).
        n_bootstrap: Number of bootstrap iterations.
        threshold: The significance threshold (p < 0.05).

    Returns:
        Dict mapping feature names to their significance rates.
    """
    n_samples = len(df)
    significance_counts = {col: 0 for col in feature_cols}
    p_values_list = {col: [] for col in feature_cols}

    logger.info(f"Starting bootstrap analysis with {n_bootstrap} iterations...")

    for i in range(n_bootstrap):
        # Resample with replacement
        bootstrap_indices = np.random.choice(n_samples, size=n_samples, replace=True)
        boot_df = df.iloc[bootstrap_indices]

        X = boot_df[feature_cols]
        y = boot_df[target_col]

        # Add constant for intercept
        X_with_const = sm.add_constant(X)

        try:
            # Fit OLS
            model = sm.OLS(y, X_with_const).fit()

            # Extract p-values for features (excluding intercept)
            # The p-values are in model.pvalues, indexed by column names
            for col in feature_cols:
                p_val = model.pvalues[col]
                p_values_list[col].append(p_val)
                if p_val < 0.05:
                    significance_counts[col] += 1
        except Exception as e:
            # If singular matrix or other error occurs in a bootstrap sample, skip it
            # This is common in bootstrap with small samples or collinearity
            logger.debug(f"Bootstrap sample {i} failed: {e}")
            continue

    # Calculate rates
    results = {}
    for col in feature_cols:
        valid_samples = len(p_values_list[col])
        if valid_samples > 0:
            rate = significance_counts[col] / valid_samples
            # Variance of p-values as a secondary metric
            p_var = np.var(p_values_list[col])
            results[col] = {
                'significance_rate': rate,
                'p_value_variance': p_var,
                'valid_samples': valid_samples
            }
        else:
            results[col] = {
                'significance_rate': 0.0,
                'p_value_variance': 0.0,
                'valid_samples': 0
            }

    return results

def run_sensitivity_analysis(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    thresholds: List[float],
    n_bootstrap: int = 1000
) -> pd.DataFrame:
    """
    Run the full sensitivity analysis across multiple thresholds.

    Args:
        df: Cleaned dataframe.
        target_col: Target variable name.
        feature_cols: Feature variable names.
        thresholds: List of coefficient magnitude thresholds to test.
        n_bootstrap: Number of bootstrap samples.

    Returns:
        DataFrame with columns: threshold, feature, significance_rate, p_value_variance
    """
    logger.info(f"Running sensitivity analysis for thresholds: {thresholds}")

    results_data = []

    # Note: The task description mentions "Sweep decision thresholds (absolute regression coefficient magnitude)".
    # However, the calculation defined is "fraction of 1000 bootstrap samples where p < 0.05".
    # The p-value calculation itself does not depend on a coefficient magnitude threshold.
    # The "threshold" in the output likely refers to the specific coefficient magnitude
    # we are testing for stability, OR it is a misinterpretation in the prompt.
    # Given the prompt says "For each threshold, calculate... significance rate",
    # and the significance rate is based on p < 0.05, we will iterate through the
    # provided thresholds. In a standard bootstrap sensitivity analysis, the p-value
    # significance rate is constant across coefficient magnitude thresholds unless we
    # are filtering coefficients.
    #
    # Interpretation: We will run the bootstrap once to get the distribution of p-values.
    # Then, for each threshold, we might interpret "significance rate" differently,
    # OR we simply report the p-value significance rate for each threshold (which would be identical).
    #
    # Re-reading T023: "Sweep decision thresholds (absolute regression coefficient magnitude ∈ {0.01, 0.05, 0.1}).
    # Calculation: For each threshold, calculate the 'significance rate' as the fraction of 1000 bootstrap samples where p < 0.05."
    #
    # This is slightly contradictory. The p < 0.05 condition is independent of coefficient magnitude.
    # However, to strictly follow the "Sweep" instruction and produce a CSV with a 'threshold' column,
    # we will perform the bootstrap for each threshold. Since the p-value calculation doesn't change,
    # the significance_rate will be the same for all thresholds for a given feature.
    #
    # Alternative interpretation: Perhaps the "threshold" is the p-value threshold?
    # No, the prompt says "coefficient magnitude".
    #
    # We will proceed by running the bootstrap once (optimizing performance) and then
    # repeating the result for each requested threshold to satisfy the output format.
    # If the prompt implies a more complex filter (e.g., only count if |coef| > threshold AND p < 0.05),
    # we would need the coefficient distribution too. Let's collect coefficient distributions.

    logger.info("Performing bootstrap to collect coefficient and p-value distributions...")
    n_samples = len(df)
    feature_distributions = {col: {'coefs': [], 'p_vals': []} for col in feature_cols}

    for i in range(n_bootstrap):
        bootstrap_indices = np.random.choice(n_samples, size=n_samples, replace=True)
        boot_df = df.iloc[bootstrap_indices]

        X = boot_df[feature_cols]
        y = boot_df[target_col]
        X_with_const = sm.add_constant(X)

        try:
            model = sm.OLS(y, X_with_const).fit()
            for col in feature_cols:
                feature_distributions[col]['coefs'].append(model.params[col])
                feature_distributions[col]['p_vals'].append(model.pvalues[col])
        except Exception:
            continue

    # Now process for each threshold
    for threshold in thresholds:
        for col in feature_cols:
            coefs = feature_distributions[col]['coefs']
            p_vals = feature_distributions[col]['p_vals']

            if not coefs:
                results_data.append({
                    'threshold': threshold,
                    'feature': col,
                    'significance_rate': 0.0,
                    'p_value_variance': 0.0
                })
                continue

            # The prompt says: "significance rate as the fraction of 1000 bootstrap samples where p < 0.05"
            # It does NOT say "and |coef| > threshold".
            # So the rate is simply count(p < 0.05) / N.
            # However, to make the threshold column meaningful, we will interpret the task as:
            # "Significance rate of the effect being both statistically significant (p<0.05) 
            # AND practically significant (|coef| > threshold)."
            # This is a common interpretation of "sensitivity to threshold".
            
            significant_count = 0
            for c, p in zip(coefs, p_vals):
                if p < 0.05 and abs(c) > threshold:
                    significant_count += 1

            rate = significant_count / len(coefs)
            p_var = np.var(p_vals)

            results_data.append({
                'threshold': threshold,
                'feature': col,
                'significance_rate': rate,
                'p_value_variance': p_var
            })

    return pd.DataFrame(results_data)

def main():
    """Main entry point for T023."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    metrics_path = project_root / "data" / "results" / "model_metrics.json"
    data_path = project_root / "data" / "processed" / "raw_cleaned.csv"
    output_path = project_root / "data" / "results" / "sensitivity_analysis.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading model metrics from {metrics_path}")
    try:
        metrics = load_model_metrics(metrics_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    logger.info(f"Loading cleaned data from {data_path}")
    try:
        df = load_cleaned_data(data_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise

    # Identify target and features from the data or metrics
    # Based on T014/T021, target is 'agency_score'
    target_col = 'agency_score'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data. Columns: {df.columns.tolist()}")

    # Identify features: typically the motion features
    # From T014: latency, smoothness, lead_time
    potential_features = ['latency', 'smoothness', 'lead_time']
    feature_cols = [f for f in potential_features if f in df.columns]

    if not feature_cols:
        raise ValueError("No motion features found in the dataset.")

    logger.info(f"Using features: {feature_cols}")

    # Thresholds as per T023 spec
    thresholds = [0.01, 0.05, 0.1]

    # Run analysis
    logger.info("Running sensitivity analysis...")
    result_df = run_sensitivity_analysis(
        df,
        target_col=target_col,
        feature_cols=feature_cols,
        thresholds=thresholds,
        n_bootstrap=1000
    )

    # Save output
    logger.info(f"Saving results to {output_path}")
    result_df.to_csv(output_path, index=False)

    logger.info("Sensitivity analysis completed successfully.")
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()