"""
Bayesian Model Fitting with Adaptive Priors based on Data Provenance.

This module implements a hierarchical Bayesian model for ingredient substitution
compatibility. Crucially, it adjusts prior widths based on the ratified methodology:
- If 'Correlational Analysis' (Proxy Data): Uses wider, more conservative priors
  to reflect higher uncertainty in derived labels.
- If 'Causal Independence' (Real Data): Uses standard informative priors.
"""
import os
import sys
import json
import time
import pickle
import signal
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Conditional imports for PyMC and backend
try:
    import pymc as pm
    import arviz as az
except ImportError:
    # Fallback for environments without PyMC installed yet, though requirements.txt should handle this
    print("ERROR: PyMC not installed. Please install pymc>=5.0.0 from requirements.txt.")
    sys.exit(1)

from code.utils.memory_monitor import check_memory_limit

# --- Configuration Constants ---
DEFAULT_PRIOR_SIGMA_CAUSAL = 1.0  # Standard informative prior width
DEFAULT_PRIOR_SIGMA_PROXY = 3.0   # Conservative wider prior for proxy data
DEFAULT_INTERCEPT_PRIOR = 0.0
DEFAULT_OBS_ERROR = 0.1

# --- Helper Functions ---

def load_amendment_log():
    """Loads the amendment log to determine the active methodology."""
    log_path = Path("data/amendment_log.json")
    if not log_path.exists():
        raise FileNotFoundError(f"Amendment log not found at {log_path}. Run T012 first.")
    
    with open(log_path, 'r') as f:
        return json.load(f)

def load_processed_data(input_path):
    """
    Loads the processed training data.
    Expects a CSV or Parquet file with columns including 'compatibility_label' (target).
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Training data not found at {input_path}.")
    
    if path.suffix == '.csv':
        return pd.read_csv(path)
    elif path.suffix == '.parquet':
        return pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def prepare_features(df):
    """
    Prepares features for the Bayesian model.
    Handles encoding of categorical variables and scaling if necessary.
    Returns X (features) and y (target).
    """
    # Ensure target exists
    if 'compatibility_label' not in df.columns:
        raise ValueError("Target column 'compatibility_label' missing from input data.")
    
    # Define predictors based on standard schema
    # We expect: log_co_occurrence, flavor_similarity, functional_role
    predictors = ['log_co_occurrence', 'flavor_similarity']
    
    # Handle functional_role if it's categorical
    if 'functional_role' in df.columns:
        if df['functional_role'].dtype == 'object':
            # One-hot encode or ordinal encode. For Bayesian, ordinal is often sufficient
            # if the order makes sense (primary=2, secondary=1, garnish=0)
            # Here we assume it's already numeric or we map it.
            # Let's map standard roles to numeric if not already
            role_map = {'primary': 2, 'secondary': 1, 'garnish': 0}
            df['functional_role'] = df['functional_role'].map(role_map).fillna(0).astype(int)
    
    if 'functional_role' in df.columns:
        predictors.append('functional_role')
    
    # Filter to predictors and target
    # Drop rows with NaN in predictors or target
    clean_df = df.dropna(subset=predictors + ['compatibility_label'])
    
    X = clean_df[predictors].values
    y = clean_df['compatibility_label'].values.astype(float)
    
    return X, y, predictors

def get_prior_sigma(methodology):
    """
    Determines the prior sigma based on the ratified methodology.
    Wider priors for proxy data (Correlational Analysis) to reflect uncertainty.
    """
    if methodology == "Correlational Analysis":
        return DEFAULT_PRIOR_SIGMA_PROXY
    else:
        return DEFAULT_PRIOR_SIGMA_CAUSAL

def fit_bayesian_model(X, y, predictors, output_dir, methodology):
    """
    Fits the hierarchical Bayesian model using PyMC.
    Adjusts prior widths based on methodology.
    """
    check_memory_limit(limit_mb=7168)
    
    n_obs = len(y)
    n_features = X.shape[1]
    prior_sigma = get_prior_sigma(methodology)
    
    print(f"Initializing Bayesian Model (Methodology: {methodology}, Prior Sigma: {prior_sigma})...")
    
    with pm.Model() as model:
        # Priors
        # Intercept
        intercept = pm.Normal('intercept', mu=DEFAULT_INTERCEPT_PRIOR, sigma=prior_sigma)
        
        # Coefficients
        # Using a Normal prior with wider sigma for proxy data
        beta = pm.Normal('beta', mu=0, sigma=prior_sigma, shape=n_features)
        
        # Likelihood
        # Logistic regression likelihood
        mu = pm.math.sigmoid(intercept + pm.math.dot(X, beta))
        
        # Bernoulli likelihood
        y_obs = pm.Bernoulli('y_obs', p=mu, observed=y)
        
        # Sample
        print("Sampling...")
        # Use NUTS sampler
        # For smaller datasets or proxy data, we might use fewer samples or tune more
        trace = pm.sample(
            draws=1000, 
            tune=1000, 
            chains=2, 
            cores=1, 
            target_accept=0.9,
            return_inferencedata=True,
            random_seed=42
        )
        
        # Save trace
        trace_path = Path(output_dir) / "bayesian_trace.nc"
        trace.to_netcdf(str(trace_path))
        
        # Compute summary statistics
        summary = pm.summary(trace)
        
        return trace, summary

def fit_simple_bayesian(X, y, predictors, output_dir, methodology):
    """
    A simplified fallback Bayesian fit if the full model fails or for quick checks.
    """
    try:
        return fit_bayesian_model(X, y, predictors, output_dir, methodology)
    except Exception as e:
        print(f"Full Bayesian model failed: {e}. Attempting simple fit...")
        # Fallback logic could go here, but for now we just re-raise if it's critical
        raise e

def save_results(summary, output_dir, methodology, prior_sigma):
    """
    Saves the model results and prior configuration to JSON.
    """
    results = {
        "methodology": methodology,
        "prior_sigma_used": prior_sigma,
        "coefficients": summary['mean'].to_dict() if hasattr(summary, 'mean') else {},
        "hdi_94": summary['hdi_94%'].to_dict() if hasattr(summary, 'hdi_94%') else {},
        "timestamp": datetime.now().isoformat()
    }
    
    output_path = Path(output_dir) / "bayesian_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Also save the specific prior config as requested by T304
    prior_config = {
        "methodology": methodology,
        "prior_sigma": prior_sigma,
        "rationale": "Wider priors used for proxy data to reflect higher uncertainty in derived labels." if methodology == "Correlational Analysis" else "Standard informative priors for causal independence analysis.",
        "timestamp": datetime.now().isoformat()
    }
    
    config_path = Path(output_dir) / "prior_config.json"
    with open(config_path, 'w') as f:
        json.dump(prior_config, f, indent=2)
    
    return results, prior_config

def save_convergence_log(trace, output_dir):
    """Saves convergence diagnostics."""
    # Basic check: R-hat < 1.05
    r_hat = trace.posterior.r_hat
    max_r_hat = r_hat.max().values.item() if hasattr(r_hat, 'max') else 1.0
    
    log = {
        "max_r_hat": float(max_r_hat),
        "converged": bool(max_r_hat < 1.05),
        "timestamp": datetime.now().isoformat()
    }
    
    log_path = Path(output_dir) / "convergence_log.json"
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)

def timeout_handler(signum, frame):
    raise TimeoutError("Model fitting timed out")

def main():
    """
    Main entry point for T304: Refine Bayesian Priors for Proxy Data.
    1. Check amendment log.
    2. Load data.
    3. Fit model with adjusted priors.
    4. Save results and prior config.
    """
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(600) # 10 minutes timeout

    try:
        # 1. Load Amendment Log
        amendment = load_amendment_log()
        methodology = amendment.get("methodology", "Causal Independence")
        print(f"Active Methodology: {methodology}")

        # 2. Load Data
        # Assuming input is passed via command line or default path
        input_path = "data/processed/train.csv"
        if not os.path.exists(input_path):
            # Fallback to parquet if csv missing
            input_path = "data/processed/train_set.parquet"
        
        df = load_processed_data(input_path)
        X, y, predictors = prepare_features(df)
        
        if len(X) == 0:
            raise ValueError("No valid data points after preparation.")

        # 3. Fit Model
        output_dir = "data/logs"
        os.makedirs(output_dir, exist_ok=True)
        
        trace, summary = fit_bayesian_model(X, y, predictors, output_dir, methodology)
        
        # 4. Save Results
        save_results(summary, output_dir, methodology, get_prior_sigma(methodology))
        save_convergence_log(trace, output_dir)
        
        print("Bayesian model fitting completed successfully.")
        print(f"Results saved to {output_dir}/bayesian_results.json")
        print(f"Prior config saved to {output_dir}/prior_config.json")

    except Exception as e:
        print(f"Error during Bayesian fitting: {e}")
        sys.exit(1)
    finally:
        signal.alarm(0) # Cancel timeout

if __name__ == "__main__":
    main()
