import os
import sys
import json
import time
import pickle
import signal
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
import scipy.stats as stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/bayesian_fit.log')
    ]
)
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Model fitting timed out")

def timeout_handler_no_signal(signum, frame):
    # Fallback for platforms without signal support (e.g., Windows)
    raise TimeoutError("Model fitting timed out")

def load_amendment_log() -> Dict[str, Any]:
    """Load the amendment log to determine methodology and proxy settings."""
    path = Path('data/amendment_log.json')
    if not path.exists():
        raise FileNotFoundError(f"Amendment log not found at {path}. Run T012d first.")
    with open(path, 'r') as f:
        return json.load(f)

def load_processed_data() -> pd.DataFrame:
    """
    Load the final processed dataset (ingredient_pairs.csv) produced by T018.
    This file must exist and contain the necessary columns for modeling.
    """
    path = Path('data/processed/ingredient_pairs.csv')
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}. Run T018 first.")
    
    logger.info(f"Loading processed data from {path}")
    df = pd.read_csv(path)
    
    required_cols = ['compatibility_label', 'log_co_occurrence', 'flavor_similarity', 'functional_role']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in processed data: {missing}")
    
    # Drop rows with NaN in target or predictors
    initial_len = len(df)
    df = df.dropna(subset=required_cols)
    dropped = initial_len - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing values in target/predictors.")
    
    return df

def prepare_features(df: pd.DataFrame) -> Dict[str, np.ndarray]:
    """
    Prepare features for the Bayesian model.
    - Normalize predictors to zero mean, unit variance.
    - Encode functional_role if categorical (though it's likely already numeric from T014b).
    """
    features = {}
    
    # Target
    y = df['compatibility_label'].values.astype(float)
    features['y'] = y
    
    # Predictors
    # 1. Log Co-occurrence
    x1 = df['log_co_occurrence'].values.astype(float)
    # 2. Flavor Similarity
    x2 = df['flavor_similarity'].values.astype(float)
    # 3. Functional Role
    x3 = df['functional_role'].values.astype(float)
    
    # Normalize predictors (standardization)
    # We store mean and std to reconstruct or for reporting, but model uses standardized inputs
    x1_mean, x1_std = x1.mean(), x1.std()
    x2_mean, x2_std = x2.mean(), x2.std()
    x3_mean, x3_std = x3.mean(), x3.std()
    
    if x1_std == 0: x1_std = 1.0
    if x2_std == 0: x2_std = 1.0
    if x3_std == 0: x3_std = 1.0
    
    features['X1'] = (x1 - x1_mean) / x1_std
    features['X2'] = (x2 - x2_mean) / x2_std
    features['X3'] = (x3 - x3_mean) / x3_std
    
    features['meta'] = {
        'n_samples': len(y),
        'means': {'log_co_occurrence': x1_mean, 'flavor_similarity': x2_mean, 'functional_role': x3_mean},
        'stds': {'log_co_occurrence': x1_std, 'flavor_similarity': x2_std, 'functional_role': x3_std}
    }
    
    return features

def get_prior_sigma(methodology: str) -> float:
    """
    Determine prior sigma based on methodology.
    If 'Correlational Analysis' (proxy data), use wider priors (higher sigma)
    to reflect higher uncertainty.
    """
    if methodology == "Correlational Analysis":
        logger.info("Detected Correlational Analysis methodology. Using conservative (wider) priors.")
        return 5.0  # Wider prior
    else:
        logger.info("Detected Causal Independence methodology. Using standard priors.")
        return 1.0  # Standard prior

def fit_bayesian_model(features: Dict[str, np.ndarray], sigma: float, 
                       draws: int = 500, tune: int = 500, chains: int = 2,
                       target_accept: float = 0.9) -> Dict[str, Any]:
    """
    Fit the hierarchical Bayesian logistic regression model using PyMC.
    Model:
      y ~ Bernoulli(p)
      logit(p) = alpha + beta1*X1 + beta2*X2 + beta3*X3
    
    Priors:
      alpha ~ Normal(0, sigma)
      beta ~ Normal(0, sigma)
    """
    n = features['n_samples']
    X1 = features['X1']
    X2 = features['X2']
    X3 = features['X3']
    y = features['y']
    
    logger.info(f"Starting PyMC model fitting. N={n}, Draws={draws}, Tune={tune}")
    
    with pm.Model() as model:
        # Priors
        alpha = pm.Normal('alpha', mu=0, sigma=sigma)
        beta1 = pm.Normal('beta1', mu=0, sigma=sigma)
        beta2 = pm.Normal('beta2', mu=0, sigma=sigma)
        beta3 = pm.Normal('beta3', mu=0, sigma=sigma)
        
        # Linear predictor
        mu = alpha + beta1 * X1 + beta2 * X2 + beta3 * X3
        
        # Likelihood
        y_obs = pm.Bernoulli('y_obs', logit_p=mu, observed=y)
        
        # Sample
        # Set random seed for reproducibility
        with pm.Model() as model:
            # Re-define inside context to ensure clean state if called multiple times
            pass 
        
        # Actually run sampling
        with model:
            try:
                # Set a timeout for the sampling process
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(300) # 5 minutes timeout for the sampling step
                
                trace = pm.sample(
                    draws=draws, 
                    tune=tune, 
                    chains=chains, 
                    target_accept=target_accept,
                    return_inferencedata=True,
                    random_seed=42,
                    progressbar=True
                )
                
                signal.alarm(0) # Cancel alarm
            except TimeoutError:
                logger.error("Sampling timed out. Returning partial results or raising.")
                raise
            except Exception as e:
                logger.error(f"Sampling failed with error: {e}")
                raise
    
    return trace

def fit_simple_bayesian(features: Dict[str, np.ndarray], sigma: float) -> Dict[str, Any]:
    """
    Fallback simple Bayesian fit if hierarchical is too complex or fails.
    Uses a simplified approach for robustness.
    """
    logger.warning("Falling back to simple Bayesian fit.")
    # Re-use the main model logic but with fewer draws/tune for speed if needed
    # For this implementation, we just call the main model with reduced resources
    return fit_bayesian_model(features, sigma, draws=200, tune=200, chains=1)

def save_results(trace: az.InferenceData, meta: Dict[str, Any], output_path: Path) -> None:
    """
    Save the results of the Bayesian fit to a JSON file.
    Extracts mean, std, and 94% HDI for coefficients.
    """
    logger.info(f"Saving results to {output_path}")
    
    # Convert trace to summary dataframe
    summary = az.summary(trace, var_names=['alpha', 'beta1', 'beta2', 'beta3'], hdi_prob=0.94)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'n_samples': meta['n_samples'],
        'standardization': {
            'log_co_occurrence': meta['means']['log_co_occurrence'],
            'flavor_similarity': meta['means']['flavor_similarity'],
            'functional_role': meta['means']['functional_role']
        },
        'coefficients': {}
    }
    
    # Extract coefficients
    for var in ['alpha', 'beta1', 'beta2', 'beta3']:
        if var in summary.index:
            row = summary.loc[var]
            results['coefficients'][var] = {
                'mean': float(row['mean']),
                'std': float(row['std']),
                'hdi_3%': float(row['hdi_3%']),
                'hdi_97%': float(row['hdi_97%']),
                'mcse_mean': float(row['mcse_mean']),
                'ess_bulk': float(row['ess_bulk'])
            }
        else:
            results['coefficients'][var] = None
    
    # Save as JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Results saved successfully.")

def save_convergence_log(trace: az.InferenceData, output_path: Path) -> None:
    """Save convergence diagnostics."""
    logger.info(f"Saving convergence log to {output_path}")
    diag = {
        'timestamp': datetime.now().isoformat(),
        'rhat': {},
        'ess': {}
    }
    
    summary = az.summary(trace, var_names=['alpha', 'beta1', 'beta2', 'beta3'])
    for var in ['alpha', 'beta1', 'beta2', 'beta3']:
        if var in summary.index:
            diag['rhat'][var] = float(summary.loc[var, 'r_hat'])
            diag['ess'][var] = float(summary.loc[var, 'ess_bulk'])
    
    with open(output_path, 'w') as f:
        json.dump(diag, f, indent=2)

def main():
    """Main entry point for T025."""
    try:
        # 1. Load Amendment Log
        amendment = load_amendment_log()
        methodology = amendment.get('methodology', 'Causal Independence')
        
        # 2. Load Processed Data
        df = load_processed_data()
        
        # 3. Prepare Features
        features = prepare_features(df)
        
        # 4. Determine Prior Sigma
        sigma = get_prior_sigma(methodology)
        
        # 5. Fit Model
        # Ensure output directories exist
        Path('data/logs').mkdir(parents=True, exist_ok=True)
        Path('data/final').mkdir(parents=True, exist_ok=True)
        
        trace = fit_bayesian_model(features, sigma)
        
        # 6. Save Results
        results_path = Path('data/logs/bayesian_results.json')
        save_results(trace, features['meta'], results_path)
        
        # 7. Save Convergence Log
        conv_path = Path('data/logs/bayesian_convergence.json')
        save_convergence_log(trace, conv_path)
        
        logger.info("T025: Hierarchical Bayesian Model Fit completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
