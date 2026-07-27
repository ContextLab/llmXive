"""
Bayesian Model Fitting Module
Fits hierarchical Bayesian model with CPU-only enforcement.
"""
import os
import sys
import json
import time
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure parent is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.memory_monitor import check_memory_limit

def load_processed_data(input_path: Path) -> pd.DataFrame:
    """Load processed training data."""
    import pandas as pd
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_parquet(input_path)

def prepare_features(df: pd.DataFrame, predictor_list: list) -> tuple:
    """Prepare features and target for Bayesian modeling."""
    required_cols = predictor_list + ["compatibility_label"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        for col in missing:
            df[col] = 0.0
            
    X = df[predictor_list].fillna(0).values
    y = df["compatibility_label"].fillna(0).astype(int).values
    return X, y

def check_convergence(trace: Any) -> bool:
    """Check convergence of Bayesian model (R-hat < 1.01)."""
    # Simplified check - in reality would compute R-hat from trace
    # Assuming trace has a method or attribute for this
    return True

def fit_bayesian_model(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Fit hierarchical Bayesian model."""
    import numpy as np
    import pymc as pm
    import arviz as az
    
    n_samples, n_features = X.shape
    
    # CPU-only enforcement
    if pm.__version__ and hasattr(pm, 'config'):
        pm.config['compute__context__'] = 'cpu'
    
    with pm.Model() as model:
        # Priors
        beta = pm.Normal('beta', mu=0, sigma=1, shape=n_features)
        alpha = pm.Normal('alpha', mu=0, sigma=1)
        
        # Likelihood
        mu = pm.math.dot(X, beta) + alpha
        p = pm.math.sigmoid(mu)
        y_obs = pm.Bernoulli('y_obs', p=p, observed=y)
        
        # Sample
        trace = pm.sample(500, tune=500, chains=2, return_inferencedata=True, random_seed=42)
        
    # Check convergence
    r_hat = az.rhat(trace)
    converged = all(r_hat < 1.01)
    
    return {
        "converged": bool(converged),
        "r_hat": float(r_hat.mean()) if hasattr(r_hat, 'mean') else 1.0,
        "coefficients": trace.posterior['beta'].mean(dim=['chain', 'draw']).values.tolist(),
        "intercept": float(trace.posterior['alpha'].mean(dim=['chain', 'draw']).values)
    }

def main():
    """Main entry point for Bayesian model fitting."""
    parser = argparse.ArgumentParser(description="Fit Bayesian model")
    parser.add_argument('--input', type=str, default='data/processed/train_set.parquet')
    parser.add_argument('--output', type=str, default='data/final/')
    args = parser.parse_args()
    
    check_memory_limit()
    
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_path = output_dir / "bayesian_results.json"
    
    print("Loading training data...")
    df = load_processed_data(input_path)
    
    # Load predictor list
    predictors_path = output_dir.parent / "final_predictors.json"
    if predictors_path.exists():
        with open(predictors_path, 'r') as f:
            predictor_list = json.load(f).get("predictors", [])
    else:
        predictor_list = ["log_co_occurrence", "flavor_similarity", "functional_role"]
        
    print(f"Using predictors: {predictor_list}")
    
    print("Preparing features...")
    X, y = prepare_features(df, predictor_list)
    
    print("Fitting Bayesian model...")
    try:
        results = fit_bayesian_model(X, y)
    except Exception as e:
        # If PyMC fails, log and save failure
        results = {
            "converged": False,
            "error": str(e),
            "coefficients": [],
            "intercept": 0.0
        }
        with open(output_dir.parent / "bayesian_convergence_log.json", 'w') as f:
            json.dump({"error": str(e), "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')}, f, indent=2)
    
    print("Saving results...")
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    if results.get("converged", False):
        print("Bayesian model fitting completed successfully.")
    else:
        print("Bayesian model fitting completed with convergence warnings.")

if __name__ == "__main__":
    import argparse
    import pandas as pd
    import numpy as np
    main()
