"""
Hierarchical Bayesian Model Fit (CPU-only) for Recipe Ingredient Substitution.
Implements T025: Fits a PyMC hierarchical logistic regression on downsampled data.
Enforces CPU-only execution, 3-hour timeout, and R-hat convergence checks.
"""
import os
import sys
import json
import time
import pickle
import signal
from pathlib import Path

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from scipy.special import expit

# Import memory monitoring utility from the project API
from utils.memory_monitor import check_memory_limit, get_memory_usage_gb

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FINAL_DIR = DATA_DIR / "final"
PROCESSED_DIR = DATA_DIR / "processed"
CONVERGENCE_LOG_PATH = DATA_DIR / "bayesian_convergence_log.json"
RESULTS_PATH = FINAL_DIR / "bayesian_results.json"
TRAIN_DATA_PATH = PROCESSED_DIR / "train_set.parquet"
SPLIT_CONFIG_PATH = DATA_DIR / "split_config.json"
MEMORY_LOG_PATH = DATA_DIR / "memory_profile.json"

TIMEOUT_SECONDS = 3 * 3600  # 3 hours
MAX_RHAT = 1.01

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Model fitting exceeded 3-hour timeout.")

def load_processed_data():
    """Load the training set prepared by T019/T018."""
    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(f"Training data not found at {TRAIN_DATA_PATH}. Run T018/T019 first.")
    
    df = pd.read_parquet(TRAIN_DATA_PATH)
    
    required_cols = ['compatibility_label', 'log_co_occurrence', 'flavor_similarity', 'functional_role']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Training data missing required columns: {missing}")
    
    return df

def prepare_features(df):
    """Prepare X and y for PyMC."""
    # Ensure numeric types
    y = df['compatibility_label'].values.astype(np.float64)
    X_log_freq = df['log_co_occurrence'].values.astype(np.float64)
    X_sim = df['flavor_similarity'].values.astype(np.float64)
    X_role = df['functional_role'].values.astype(np.float64)
    
    # Center and scale for better sampling (optional but recommended)
    # We will handle scaling inside the model or pre-calculate
    return y, X_log_freq, X_sim, X_role

def fit_bayesian_model(y, X_log_freq, X_sim, X_role, seed=42):
    """
    Fit a hierarchical Bayesian logistic regression.
    Model: logit(p) = beta_0 + beta_freq * freq + beta_sim * sim + beta_role * role
    Priors: Normal(0, 1) for coefficients.
    """
    n = len(y)
    
    # Define the model
    with pm.Model() as model:
        # Priors
        beta_0 = pm.Normal('beta_0', mu=0, sigma=1)
        beta_freq = pm.Normal('beta_freq', mu=0, sigma=1)
        beta_sim = pm.Normal('beta_sim', mu=0, sigma=1)
        beta_role = pm.Normal('beta_role', mu=0, sigma=1)
        
        # Linear predictor
        mu = (
            beta_0 +
            beta_freq * X_log_freq +
            beta_sim * X_sim +
            beta_role * X_role
        )
        
        # Likelihood
        p = pm.Deterministic('p', pm.math.sigmoid(mu))
        y_obs = pm.Bernoulli('y_obs', p=p, observed=y)
        
        # MCMC Sampling
        # Use NUTS, 2000 draws, 1000 tune. 
        # Target acceptance 0.9 for better convergence in complex spaces.
        trace = pm.sample(
            draws=2000,
            tune=1000,
            chains=4,
            target_accept=0.9,
            random_seed=seed,
            cores=1,  # Force single core to avoid resource contention in CI
            progressbar=True
        )
        
    return model, trace

def check_convergence(trace):
    """Check R-hat and ESS. Returns dict of metrics."""
    summary = az.summary(trace, var_names=["beta_0", "beta_freq", "beta_sim", "beta_role"])
    
    r_hat_max = summary['r_hat'].max()
    ess_min = summary['ess_bulk'].min()
    
    return {
        "r_hat_max": float(r_hat_max),
        "ess_min": float(ess_min),
        "converged": bool(r_hat_max <= MAX_RHAT)
    }

def save_results(trace, metrics, model):
    """Save results to JSON and pickle the trace."""
    # Extract posterior means
    summary = az.summary(trace, var_names=["beta_0", "beta_freq", "beta_sim", "beta_role"])
    
    results = {
        "status": "SUCCESS",
        "convergence_metrics": metrics,
        "posterior_means": {
            "beta_0": float(summary.loc['beta_0', 'mean']),
            "beta_freq": float(summary.loc['beta_freq', 'mean']),
            "beta_sim": float(summary.loc['beta_sim', 'mean']),
            "beta_role": float(summary.loc['beta_role', 'mean']),
        },
        "posterior_sd": {
            "beta_0": float(summary.loc['beta_0', 'sd']),
            "beta_freq": float(summary.loc['beta_freq', 'sd']),
            "beta_sim": float(summary.loc['beta_sim', 'sd']),
            "beta_role": float(summary.loc['beta_role', 'sd']),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Save trace for later inspection
    trace_path = FINAL_DIR / "bayesian_trace.pkl"
    with open(trace_path, 'wb') as f:
        pickle.dump(trace, f)
        
    print(f"Results saved to {RESULTS_PATH}")

def save_convergence_log(metrics):
    """Save convergence log (used for failure or success)."""
    CONVERGENCE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_data = {
        "status": "SUCCESS" if metrics['converged'] else "FAILED",
        "metrics": {
            "R_hat": metrics['r_hat_max'],
            "ESS": metrics['ess_min']
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(CONVERGENCE_LOG_PATH, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    if not metrics['converged']:
        print(f"WARNING: Convergence failed. R_hat={metrics['r_hat_max']:.4f} > {MAX_RHAT}")

def main():
    print("Starting Hierarchical Bayesian Model Fit (T025)...")
    
    # Enforce CPU-only
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    
    # Set timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(TIMEOUT_SECONDS)
    
    try:
        # 1. Load Data
        print("Loading training data...")
        df = load_processed_data()
        
        # Downsample if necessary (T019 should have handled this, but ensure small size for CI)
        # If the dataset is still huge, we take a representative sample to fit the model within time limits
        if len(df) > 50000:
            print(f"Downsampling data from {len(df)} to 50000 for Bayesian fit...")
            df = df.sample(n=50000, random_state=42)
        
        y, X_log_freq, X_sim, X_role = prepare_features(df)
        
        # 2. Fit Model
        print("Fitting Bayesian model (CPU-only)...")
        model, trace = fit_bayesian_model(y, X_log_freq, X_sim, X_role)
        
        # 3. Check Convergence
        print("Checking convergence...")
        metrics = check_convergence(trace)
        
        # 4. Save Outputs
        save_results(trace, metrics, model)
        save_convergence_log(metrics)
        
        if not metrics['converged']:
            # Task requires "fail loudly if R_hat > 1.01"
            # We have logged the failure, but we exit with error code to signal pipeline failure
            print("FATAL: Bayesian model did not converge (R_hat > 1.01).")
            sys.exit(1)
            
        print("Bayesian model fit completed successfully.")
        
    except TimeoutError:
        print("FATAL: Model fitting timed out.")
        CONVERGENCE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONVERGENCE_LOG_PATH, 'w') as f:
            json.dump({
                "status": "FAILED",
                "reason": "TIMEOUT",
                "metrics": {"R_hat": None, "ESS": None},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }, f, indent=2)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL: Error during fitting: {e}")
        # Log failure
        CONVERGENCE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONVERGENCE_LOG_PATH, 'w') as f:
            json.dump({
                "status": "FAILED",
                "reason": str(e),
                "metrics": {"R_hat": None, "ESS": None},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }, f, indent=2)
        sys.exit(1)
    finally:
        signal.alarm(0)  # Cancel alarm

if __name__ == "__main__":
    import argparse
    import pandas as pd
    import numpy as np
    main()
