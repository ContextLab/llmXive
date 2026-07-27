import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from config import get_project_root, get_config_dict

def load_user_track_pairs(data_dir: str) -> pd.DataFrame:
    """Loads the user-track pair dataset."""
    file_path = Path(data_dir) / "user_track_pairs.parquet"
    return pd.read_parquet(file_path)

def fit_mixed_model(df: pd.DataFrame) -> smf.MixedLMResults:
    """Fits a linear mixed-effects model."""
    model = smf.ols("mean_vividness ~ adolescent_exposure_ratio + popularity", data=df, groups=df["user_id"]).fit()
    return model

def calculate_vif(df: pd.DataFrame, exog_name: str) -> float:
  """Calculates Variance Inflation Factor (VIF)."""
  from statsmodels.stats.outliers_influence import variance_inflation_factor
  X = df[exog_name]
  return variance_inflation_factor(X)

def run_bootstrap_test(df: pd.DataFrame, model, n_iterations: int = 1000) -> np.ndarray:
    """Runs a parametric bootstrap test."""
    residuals = model.resid
    predictions = model.fittedvalues
    random_state = get_config_dict().get("RANDOM_SEED", 42)

    t_stats = []
    for _ in range(n_iterations):
        resampled_residuals = np.random.choice(residuals, size=len(residuals), replace=True)
        y_bootstrapped = predictions + resampled_residuals
        df_bootstrapped = df.copy()
        df_bootstrapped["mean_vividness"] = y_bootstrapped

        model_bootstrapped = smf.ols("mean_vividness ~ adolescent_exposure_ratio + popularity", data=df_bootstrapped, groups=df_bootstrapped["user_id"]).fit()
        t_stats.append(model_bootstrapped.params['adolescent_exposure_ratio'] / model_bootstrapped.bse['adolescent_exposure_ratio'])

    return np.array(t_stats)


def main():
    """Main function to run the analysis."""
    config = get_config_dict()
    data_dir = os.path.join(get_project_root(), "data", "processed")

    # Load data
    df = load_user_track_pairs(data_dir)

    # Fit model
    model = fit_mixed_model(df)

    # Calculate VIF
    vif_exposure = calculate_vif(df, 'adolescent_exposure_ratio')
    vif_popularity = calculate_vif(df, 'popularity')

    # Run bootstrap test
    bootstrap_results = run_bootstrap_test(df, model)

    # Calculate p-value
    observed_t = model.params['adolescent_exposure_ratio'] / model.bse['adolescent_exposure_ratio']
    p_value = (np.sum(np.abs(bootstrap_results) >= np.abs(observed_t)) / len(bootstrap_results)) * 2

    # Create a summary DataFrame
    summary_data = {
        'coefficient': [model.params['adolescent_exposure_ratio'], model.params['popularity']],
        'se': [model.bse['adolescent_exposure_ratio'], model.bse['popularity']],
        'pvalue': [model.pvalues['adolescent_exposure_ratio'], model.pvalues['popularity']],
        'vif': [vif_exposure, vif_popularity]
    }

    summary_df = pd.DataFrame(summary_data)
    summary_df.index = ['adolescent_exposure_ratio', 'popularity']

    # Save results
    output_path = os.path.join(get_project_root(), "data", "final", "regression_summary.csv")
    summary_df.to_csv(output_path)

    logging.info(f"Regression summary saved to: {output_path}")
    logging.info(f"P-value of adolescent_exposure_ratio: {p_value}")
