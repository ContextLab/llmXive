import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from sklearn.decomposition import PCA
from scipy import stats

from config import get_processed_data_path, get_compute_data_path, get_figures_path
from utils.logging import setup_logging, log_compliance_check

# Ensure reproducibility
from utils.seeds import set_seed
set_seed(42)

logger = logging.getLogger(__name__)

def load_kinetic_metrics() -> pd.DataFrame:
    """Load kinetic metrics from processed data."""
    metrics_path = get_processed_data_path() / "kinetic_metrics.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Kinetic metrics file not found: {metrics_path}")
    return pd.read_csv(metrics_path)

def load_solvent_models() -> pd.DataFrame:
    """Load solvent model data (solvation energy) from compute data."""
    models_path = get_compute_data_path() / "solvent_solvation.csv"
    if not models_path.exists():
        raise FileNotFoundError(f"Solvent models file not found: {models_path}")
    return pd.read_csv(models_path)

def load_solvent_properties() -> Dict[str, float]:
    """Load dielectric constants from the chemical data loader."""
    try:
        from data.loaders import get_solvent_properties as get_props
        # We need to fetch for all solvents present in the dataset
        # This is a simplified fetch; in a real scenario, we'd iterate or pass a list
        # For now, we assume the loader can handle a batch or we fetch individually
        # The loader API `get_solvent_properties` typically takes a name.
        # We will resolve this in the merge step by iterating.
        return get_props
    except ImportError:
        # Fallback if loader is not fully wired in this specific snippet context
        # In a full run, the loader is expected to be available.
        logger.warning("Loader import failed; attempting manual resolution or expecting data merge.")
        return {}

def compute_polarity_index(
    df: pd.DataFrame,
    solvation_energy_col: str = "solvation_free_energy",
    dielectric_col: str = "dielectric_constant"
) -> pd.DataFrame:
    """
    Compute a PCA-derived 'Solvent Polarity Index' to avoid tautology.
    Uses Solvation Energy and Dielectric Constant as features.
    """
    features = [solvation_energy_col, dielectric_col]
    # Ensure features exist
    if not all(col in df.columns for col in features):
        missing = [c for c in features if c not in df.columns]
        raise ValueError(f"Missing features for PCA: {missing}")

    # Handle missing values
    data_subset = df[features].dropna()
    if len(data_subset) < 2:
        raise ValueError("Insufficient data points for PCA (need >= 2).")

    pca = PCA(n_components=1)
    # Standardize data is usually good practice for PCA
    scaler_data = (data_subset - data_subset.mean()) / data_subset.std()
    principal_components = pca.fit_transform(scaler_data)

    # Create a series aligned with the original index
    # We need to map the PC1 values back to the original dataframe rows
    # Since dropna removed rows, we need to be careful.
    # A safer approach: fit on the subset, then transform the full set (with NaNs) if possible,
    # or simply re-index.
    
    # Let's create a temporary dataframe for the PCA result
    temp_df = data_subset.copy()
    temp_df['polarity_index'] = principal_components[:, 0]
    
    # Merge back to original
    result_df = df.merge(temp_df[['polarity_index']], left_index=True, right_index=True, how='left')
    
    logger.info(f"PCA Variance Explained: {pca.explained_variance_ratio_[0]:.4f}")
    return result_df

def run_bayesian_correlation(
    df: pd.DataFrame,
    predictor_col: str = "polarity_index",
    target_col: str = "mean_lifetime",
    n_draws: int = 2000,
    n_tune: int = 1000
) -> Tuple[az.InferenceData, Dict[str, Any]]:
    """
    Perform Bayesian Hierarchical Modeling (BHM) to correlate lifetime with Solvability/Polarity.
    Model: y ~ Normal(alpha + beta * X, sigma)
    Priors:
      alpha ~ Normal(0, 10)
      beta ~ Normal(0, 5)
      sigma ~ HalfCauchy(5)
    """
    X = df[predictor_col].values
    y = df[target_col].values

    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        raise ValueError("Data contains NaN values. Cannot run Bayesian model.")

    logger.info(f"Running Bayesian Correlation with {len(y)} data points.")
    logger.info(f"Predictor: {predictor_col}, Target: {target_col}")

    with pm.Model() as model:
        # Priors
        alpha = pm.Normal("alpha", mu=0, sigma=10)
        beta = pm.Normal("beta", mu=0, sigma=5)
        sigma = pm.HalfCauchy("sigma", beta=5)

        # Likelihood
        mu = alpha + beta * X
        obs = pm.Normal("obs", mu=mu, sigma=sigma, observed=y)

        # Sample
        trace = pm.sample(
            draws=n_draws,
            tune=n_tune,
            chains=4,
            target_accept=0.9,
            return_inferencedata=True,
            random_seed=42
        )

    return trace, {
        "model_summary": pm.summary(trace).to_dict(),
        "n_draws": n_draws,
        "n_tune": n_tune
    }

def write_correlation_results(
    trace: az.InferenceData,
    df: pd.DataFrame,
    output_path: Path,
    posterior_summary: Dict[str, Any]
) -> None:
    """Write posterior distributions and summary metrics to JSON."""
    summary_df = pm.summary(trace)
    
    # Extract slope and intercept stats
    slope_stats = summary_df.loc["beta"]
    intercept_stats = summary_df.loc["alpha"]
    sigma_stats = summary_df.loc["sigma"]

    # Calculate Bayesian R^2
    # Using the method from Vehtari et al. (2017) or simple posterior predictive check
    # Here we approximate R^2 using posterior predictive means
    y_obs = df["mean_lifetime"].values
    # Get posterior predictive mean
    ppc = pm.sample_posterior_predictive(trace, var_names=["obs"], random_seed=42)
    y_pred_mean = ppc.posterior["obs"].mean(dim=["chain", "draw"]).values
    
    ss_res = np.sum((y_obs - y_pred_mean) ** 2)
    ss_tot = np.sum((y_obs - np.mean(y_obs)) ** 2)
    bayesian_r2 = 1 - (ss_res / ss_tot)

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_type": "Bayesian Linear Regression (BHM)",
        "predictor": "Solvent Polarity Index (PCA-derived)",
        "target": "Singlet-Radical-Pair Lifetime",
        "bayesian_r2": float(bayesian_r2),
        "intercept": {
            "mean": float(intercept_stats["mean"]),
            "std": float(intercept_stats["sd"]),
            "hdi_3%": float(intercept_stats["hdi_3%"]),
            "hdi_97%": float(intercept_stats["hdi_97%"])
        },
        "slope": {
            "mean": float(slope_stats["mean"]),
            "std": float(slope_stats["sd"]),
            "hdi_3%": float(slope_stats["hdi_3%"]),
            "hdi_97%": float(slope_stats["hdi_97%"])
        },
        "sigma": {
            "mean": float(sigma_stats["mean"]),
            "std": float(sigma_stats["sd"]),
            "hdi_3%": float(sigma_stats["hdi_3%"]),
            "hdi_97%": float(sigma_stats["hdi_97%"])
        },
        "n_observations": len(df),
        "posterior_summary": posterior_summary
    }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Correlation results written to {output_path}")

def generate_regression_plot(
    trace: az.InferenceData,
    df: pd.DataFrame,
    output_path: Path,
  ) -> None:
      """Generate a regression plot with credible intervals."""
      import matplotlib.pyplot as plt
      import seaborn as sns

      plt.style.use("seaborn-v0_8-whitegrid")
      fig, ax = plt.subplots(figsize=(10, 6))

      # Scatter plot of data
      sns.scatterplot(
          x=df["polarity_index"],
          y=df["mean_lifetime"],
          ax=ax,
          s=100,
          label="Experimental Data",
          color="black",
          zorder=10
      )

      # Get posterior samples for the regression line
      alpha_samples = trace.posterior["alpha"].values.flatten()
      beta_samples = trace.posterior["beta"].values.flatten()
      x_vals = np.linspace(df["polarity_index"].min(), df["polarity_index"].max(), 100)

      # Plot several regression lines to show uncertainty
      # We take a subset of samples to avoid overcrowding
      n_lines = min(50, len(alpha_samples))
      indices = np.random.choice(len(alpha_samples), n_lines, replace=False)
      
      for idx in indices:
          y_vals = alpha_samples[idx] + beta_samples[idx] * x_vals
          ax.plot(x_vals, y_vals, color="blue", alpha=0.05, linewidth=1)

      # Plot the mean regression line
      mean_alpha = np.mean(alpha_samples)
      mean_beta = np.mean(beta_samples)
      y_mean = mean_alpha + mean_beta * x_vals
      ax.plot(x_vals, y_mean, color="red", linewidth=2, label="Posterior Mean")

      # Calculate 95% CI for the line
      y_lower = np.percentile([a + b * x for a, b in zip(alpha_samples, beta_samples)], 2.5, axis=0)
      y_upper = np.percentile([a + b * x for a, b in zip(alpha_samples, beta_samples)], 97.5, axis=0)
      ax.fill_between(x_vals, y_lower, y_upper, color="red", alpha=0.2, label="95% Credible Interval")

      ax.set_xlabel("Solvent Polarity Index (PCA-derived)")
      ax.set_ylabel("Mean Lifetime (ns)")
      ax.set_title("Bayesian Correlation: Solvent Polarity vs. Radical-Pair Lifetime")
      ax.legend()

      plt.tight_layout()
      plt.savefig(output_path, dpi=300)
      plt.close()
      logger.info(f"Regression plot saved to {output_path}")

def main():
    setup_logging()
    logger.info("Starting Bayesian Correlation Analysis (T030a)")

    try:
        # 1. Load Data
        kinetic_df = load_kinetic_metrics()
        solvent_models_df = load_solvent_models()

        # Merge on solvent name
        # Assume 'solvent_name' is the key in both
        if "solvent_name" not in kinetic_df.columns or "solvent_name" not in solvent_models_df.columns:
            raise ValueError("Missing 'solvent_name' column in input dataframes.")

        merged_df = pd.merge(kinetic_df, solvent_models_df, on="solvent_name", how="inner")

        if len(merged_df) < 3:
            raise ValueError(f"Insufficient data for analysis after merge. Found {len(merged_df)} rows. Need >= 3.")

        # 2. Compute Polarity Index (PCA)
        # We need to ensure dielectric constant is available.
        # If not in solvent_models_df, we must fetch it.
        if "dielectric_constant" not in merged_df.columns:
            # Attempt to fetch from loaders
            logger.info("Dielectric constant missing in merged data. Fetching from loader...")
            # This is a simplification. In a real robust pipeline, we'd map names to values efficiently.
            # For this implementation, we assume the loader or data source has it.
            # If the task T006/T008 is fully implemented, we can call get_solvent_properties(name).
            # Here we simulate the fetch if the column is missing, assuming the loader is available.
            try:
                from data.loaders import get_solvent_properties
                diel_map = {}
                for name in merged_df["solvent_name"].unique():
                    try:
                        props = get_solvent_properties(name)
                        diel_map[name] = props.get("dielectric_constant")
                    except Exception as e:
                        logger.warning(f"Could not fetch dielectric constant for {name}: {e}")
                        diel_map[name] = np.nan
                merged_df["dielectric_constant"] = merged_df["solvent_name"].map(diel_map)
            except ImportError:
                raise RuntimeError("Could not fetch dielectric constants. Ensure T008 is complete and data is available.")

        # 3. Run PCA
        final_df = compute_polarity_index(
            merged_df,
            solvation_energy_col="solvation_free_energy",
            dielectric_col="dielectric_constant"
        )

        # 4. Run Bayesian Model
        trace, summary = run_bayesian_correlation(final_df)

        # 5. Write Results
        output_dir = get_processed_data_path()
        output_json = output_dir / "correlation_results.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        write_correlation_results(trace, final_df, output_json, summary)

        # 6. Generate Plot
        figures_dir = get_figures_path()
        figures_dir.mkdir(parents=True, exist_ok=True)
        plot_path = figures_dir / "regression_plot.png"
        generate_regression_plot(trace, final_df, plot_path)

        logger.info("T030a completed successfully.")

    except Exception as e:
        logger.error(f"Task T030a failed: {e}")
        raise

if __name__ == "__main__":
    main()
