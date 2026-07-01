import os
import pandas as pd
import numpy as np
from pathlib import Path
import statsmodels.api as sm
import json
from typing import List, Dict, Any
import logging

# Import logging config from utils if available, otherwise fallback to basic config
try:
    from utils.logging_config import get_logger
    logger = get_logger("sensitivity_analysis")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("sensitivity_analysis")

def bootstrap_sensitivity_check(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    thresholds: List[float],
    n_bootstraps: int = 1000,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Perform sensitivity analysis by bootstrapping the regression model
    and checking significance rates across different coefficient thresholds.

    Logic:
    1. For each bootstrap sample:
       - Fit OLS model
       - Extract coefficients and p-values
    2. For each threshold in thresholds:
       - Count how many bootstrap samples had |coefficient| > threshold AND p < 0.05
       - Calculate significance rate (count / n_bootstraps)
    3. Calculate variance of p-values across bootstraps for each feature.

    Args:
        df: Cleaned dataframe with features and target.
        feature_cols: List of feature column names.
        target_col: Name of the target column (agency_score).
        thresholds: List of coefficient magnitude thresholds to sweep.
        n_bootstraps: Number of bootstrap iterations.
        random_state: Random seed for reproducibility.

    Returns:
        DataFrame with columns: threshold, significance_rate, p_value_variance
    """
    np.random.seed(random_state)
    n_samples = len(df)
    
    # Storage for results
    p_values_storage = {col: [] for col in feature_cols}
    significance_counts = {thresh: 0 for thresh in thresholds}

    logger.info(f"Starting bootstrap sensitivity analysis with {n_bootstraps} iterations...")

    for i in range(n_bootstraps):
        # Bootstrap sample (sampling with replacement)
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        boot_df = df.iloc[indices]

        X = sm.add_constant(boot_df[feature_cols])
        y = boot_df[target_col]

        try:
            model = sm.OLS(y, X).fit()
            p_vals = model.pvalues[feature_cols]
            coeffs = model.params[feature_cols]

            # Store p-values for variance calculation
            for col in feature_cols:
                p_values_storage[col].append(p_vals[col])

            # Check significance against thresholds
            # We check if ANY feature meets the threshold criteria for this bootstrap
            # Or we can aggregate per feature. The task asks for "significance rate" generally.
            # Interpretation: Rate at which the model finds significant effects > threshold.
            
            for thresh in thresholds:
                # Check if any feature has |coeff| > thresh AND p < 0.05
                # This measures robustness of finding *any* effect above threshold
                found_significant = False
                for col in feature_cols:
                    if abs(coeffs[col]) > thresh and p_vals[col] < 0.05:
                        found_significant = True
                        break
                if found_significant:
                    significance_counts[thresh] += 1

        except Exception as e:
            logger.warning(f"Bootstrap iteration {i} failed: {e}")
            continue

    # Calculate results
    results = []
    for thresh in sorted(thresholds):
        rate = significance_counts[thresh] / n_bootstraps
        results.append({
            'threshold': thresh,
            'significance_rate': rate
        })
    
    results_df = pd.DataFrame(results)

    # Calculate p-value variance per feature (aggregate across features for a single metric?)
    # The task asks for 'p_value_variance' in the output.
    # We will calculate the average variance of p-values across all features for robustness.
    variances = []
    for col in feature_cols:
        if len(p_values_storage[col]) > 1:
            variances.append(np.var(p_values_storage[col]))
    
    if variances:
        avg_p_value_variance = np.mean(variances)
    else:
        avg_p_value_variance = np.nan

    results_df['p_value_variance'] = avg_p_value_variance

    return results_df

def run_sensitivity_analysis(
    data_path: str,
    output_path: str,
    feature_cols: List[str] = None,
    target_col: str = "agency_score",
    thresholds: List[float] = None,
    n_bootstraps: int = 1000
):
    """
    Main entry point to run sensitivity analysis.
    
    Reads cleaned data, runs bootstrap sensitivity check, and saves results.
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.1]
    
    logger.info(f"Loading data from {data_path}")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    # Validate columns
    missing_cols = [c for c in feature_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing feature columns in data: {missing_cols}")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")

    logger.info(f"Running sensitivity analysis on features: {feature_cols}")
    results_df = bootstrap_sensitivity_check(
        df=df,
        feature_cols=feature_cols,
        target_col=target_col,
        thresholds=thresholds,
        n_bootstraps=n_bootstraps
    )

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving results to {output_path}")
    results_df.to_csv(output_path, index=False)
    logger.info("Sensitivity analysis complete.")

def main():
    """
    CLI entry point for T023.
    Reads from data/processed/cleaned_data.csv and outputs to data/results/sensitivity_analysis.csv
    """
    # Define paths based on project structure
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "data" / "processed" / "cleaned_data.csv"
    output_path = project_root / "data" / "results" / "sensitivity_analysis.csv"

    # Default features based on T014/T017 schema (latency, smoothness, lead_time)
    feature_cols = ["latency", "smoothness", "lead_time"]
    
    # Filter out features that might be missing in the CSV if lead_time is optional
    # We read the CSV first to check columns if needed, but assume standard schema.
    # To be safe, we will check existence in the file before running.
    
    try:
        df_check = pd.read_csv(data_path)
        available_features = [f for f in feature_cols if f in df_check.columns]
        if not available_features:
            # Fallback to all numeric columns except target if specific ones missing
            numeric_cols = df_check.select_dtypes(include=[np.number]).columns.tolist()
            available_features = [c for c in numeric_cols if c != "agency_score"]
        
        if not available_features:
            raise ValueError("No valid feature columns found for regression.")
            
        run_sensitivity_analysis(
            data_path=str(data_path),
            output_path=str(output_path),
            feature_cols=available_features,
            target_col="agency_score",
            thresholds=[0.01, 0.05, 0.1],
            n_bootstraps=1000
        )
    except FileNotFoundError:
        logger.error(f"Required data file not found: {data_path}")
        raise
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()