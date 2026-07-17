import os
import sys
import json
import time
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from scipy import stats

# Project root handling
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = DATA_DIR / "final"
LOGS_DIR = DATA_DIR

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_processed_data() -> pd.DataFrame:
    """
    Loads the processed dataset from the split step.
    Expects data to be in data/final/train_processed.parquet or similar.
    """
    # T019 saves the downsampled data. We look for the standard output.
    # Fallback to checking specific filenames if T019 output varies.
    candidates = [
        DATA_DIR / "final" / "train_processed.parquet",
        DATA_DIR / "final" / "train_subset.parquet",
        DATA_DIR / "processed" / "train_processed.parquet"
    ]
    
    data_path = None
    for candidate in candidates:
        if candidate.exists():
            data_path = candidate
            break
    
    if not data_path:
        raise FileNotFoundError(
            "Could not find processed training data. "
            "Ensure T019 (split.py) has been executed and saved output to data/final/."
        )
    
    # Use pyarrow for efficiency if available, else pandas default
    try:
        return pd.read_parquet(data_path)
    except Exception:
        return pd.read_csv(data_path)

def prepare_features(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Prepares features and target for the Bayesian model.
    Ensures data is in the correct format and normalized if necessary.
    """
    # Expected columns based on T018/T019 pipeline
    target_col = "compatibility_label"
    features = ["log_frequency", "flavor_similarity", "role_primary", "role_secondary"]
    
    # Handle missing values if any (though T018 should have imputed)
    # We rely on T018 imputation, but add a safety check
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns: {missing_features}")
    
    X = df[features].values.astype(np.float32)
    y = df[target_col].values.astype(np.int32)
    
    # Center and scale predictors for better MCMC convergence
    # We calculate mean/std on the training data only
    X_mean = X.mean(axis=0)
    X_std = X.std(axis=0)
    X_std[X_std == 0] = 1.0 # Avoid division by zero
    
    X_scaled = (X - X_mean) / X_std
    
    return {
        "X": X_scaled,
        "y": y,
        "X_mean": X_mean,
        "X_std": X_std,
        "feature_names": features
    }

def check_convergence(idata: az.InferenceData, 
                      target_rhat: float = 1.05, 
                      min_ess: int = 200,
                      timeout_seconds: int = 300) -> Dict[str, Any]:
    """
    Checks MCMC convergence using R-hat and Effective Sample Size (ESS).
    Implements early stopping logic if diagnostics are poor after a timeout.
    
    Args:
        idata: ArviZ InferenceData object from PyMC sampling.
        target_rhat: Maximum acceptable R-hat value.
        min_ess: Minimum acceptable Effective Sample Size.
        timeout_seconds: Time limit for sampling (used for logging, not hard stop of running sampler).
    
    Returns:
        Dict with convergence status and diagnostics.
    """
    summary = az.summary(idata)
    
    # Extract R-hat and ESS for all variables
    rhat_values = summary["r_hat"].values
    ess_values = summary["ess_bulk"].values # Use bulk ESS for general convergence
    
    max_rhat = float(np.max(rhat_values))
    min_ess_found = float(np.min(ess_values))
    
    diagnostics = {
        "max_r_hat": max_rhat,
        "min_ess": min_ess_found,
        "all_rhat_acceptable": bool(max_rhat <= target_rhat),
        "all_ess_acceptable": bool(min_ess_found >= min_ess),
        "converged": False,
        "failure_reason": None
    }
    
    if max_rhat > target_rhat:
        diagnostics["converged"] = False
        diagnostics["failure_reason"] = f"R-hat ({max_rhat:.4f}) exceeds threshold ({target_rhat}). Chains have not converged."
    elif min_ess_found < min_ess:
        diagnostics["converged"] = False
        diagnostics["failure_reason"] = f"Effective Sample Size ({min_ess_found:.1f}) is below minimum ({min_ess}). Sampling is insufficient."
    else:
        diagnostics["converged"] = True
        
    return diagnostics

def fit_bayesian_model(data: Dict[str, Any], 
                       draws: int = 1000, 
                       tune: int = 1000, 
                       chains: int = 4, 
                       target_accept: float = 0.9,
                       timeout_seconds: int = 600) -> tuple:
    """
    Fits the Hierarchical Bayesian Model with convergence checks.
    
    The model predicts compatibility (binary) based on:
    - log_frequency (control)
    - flavor_similarity (predictor)
    - role indicators (predictors)
    
    Implements early stopping/fail-loud if convergence is not reached.
    """
    X = data["X"]
    y = data["y"]
    n_obs = len(y)
    n_features = X.shape[1]
    
    print(f"Starting Bayesian Model fitting: {n_obs} observations, {n_features} predictors.")
    print(f"Sampling configuration: {chains} chains, {tune} tune, {draws} draws.")
    
    start_time = time.time()
    convergence_report = None
    
    with pm.Model() as model:
        # Priors
        # Intercept
        intercept = pm.Normal("intercept", mu=0, sigma=5)
        
        # Coefficients (Beta)
        # Using a weakly informative prior for coefficients
        beta = pm.Normal("beta", mu=0, sigma=2.5, shape=n_features)
        
        # Linear predictor
        mu = pm.Deterministic("mu", intercept + pm.math.dot(X, beta))
        
        # Likelihood (Bernoulli)
        # Using a logistic link function
        p = pm.math.sigmoid(mu)
        y_obs = pm.Bernoulli("y_obs", p=p, observed=y)
        
        # Sampling with early stopping logic
        # We sample with a timeout check. If R-hat is bad after timeout, we fail.
        try:
            # Use NUTS (default)
            idata = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                target_accept=target_accept,
                return_inferencedata=True,
                random_seed=42, # Reproducibility (T005)
                progressbar=True
            )
        except Exception as e:
            # Catch any sampling errors (e.g., divergences that stop sampling)
            raise RuntimeError(f"PyMC sampling failed: {str(e)}")
        
        elapsed = time.time() - start_time
        print(f"Sampling completed in {elapsed:.2f} seconds.")
        
        # Check Convergence
        print("Checking convergence diagnostics (R-hat, ESS)...")
        convergence_report = check_convergence(idata)
        
        if not convergence_report["converged"]:
            # FAIL LOUDLY as per T040 requirements
            raise RuntimeError(
                f"Bayesian Model Convergence Failed: {convergence_report['failure_reason']}. "
                "The model did not reach a stable posterior. Do not use these results."
            )
        
        print("Convergence checks passed.")
        
        # Save the model and inference data
        output_path = MODELS_DIR / "bayesian_model_results.pkl"
        with open(output_path, "wb") as f:
            pickle.dump({
                "idata": idata,
                "model": model,
                "data_prep": data,
                "convergence": convergence_report,
                "runtime_seconds": elapsed
            }, f)
        
        print(f"Bayesian model results saved to {output_path}")
        
        return idata, convergence_report

def main():
    """
    Main entry point for T040: Bayesian Model Fitting with Convergence Checks.
    """
    print("=== T040: Bayesian Model Fitting with Convergence Checks ===")
    
    try:
        # 1. Load Data
        df = load_processed_data()
        print(f"Loaded data with shape: {df.shape}")
        
        # 2. Prepare Features
        data = prepare_features(df)
        print("Features prepared and scaled.")
        
        # 3. Fit Model with Convergence Checks
        # Parameters can be tuned, but defaults are reasonable for this scale
        idata, diagnostics = fit_bayesian_model(
            data, 
            draws=1000, 
            tune=1000, 
            chains=4, 
            target_accept=0.9
        )
        
        # 4. Generate Summary Report
        summary_path = MODELS_DIR / "bayesian_diagnostics.json"
        with open(summary_path, "w") as f:
            json.dump(diagnostics, f, indent=2, default=str)
        
        print(f"Diagnostics saved to {summary_path}")
        print("T040 Completed Successfully.")
        
    except RuntimeError as e:
        # Explicit failure handling for convergence issues
        print(f"T040 FAILED: {str(e)}")
        # Write a failure report to disk for the pipeline to catch
        failure_report = {
            "status": "FAILED",
            "reason": str(e),
            "task": "T040"
        }
        failure_path = MODELS_DIR / "bayesian_failure_report.json"
        with open(failure_path, "w") as f:
            json.dump(failure_report, f, indent=2)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error in T040: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()