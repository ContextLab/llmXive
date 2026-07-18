"""
Bayesian Model Execution and Convergence Handling.

Implements the PyMC3/PyMC model structure and handles convergence failures
by falling back to Maximum Likelihood Estimation (MLE) and flagging results
as inconclusive.
"""
import os
import sys
import logging
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from scipy.optimize import minimize
from sklearn.linear_model import LinearRegression

# Import project utilities
from config import get_path, init_random_seeds
from utils.logging_utils import get_logger, log_pipeline_step
from utils.schemas import ModelResult, validate_model_result_schema

# Configure logging
logger = get_logger(__name__)

def load_preprocessed_data() -> pd.DataFrame:
    """
    Load preprocessed data from the data/processed directory.
    Expects 'merged_data.csv' with salience and foundation scores.
    """
    data_path = get_path("data/processed/merged_data.csv")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}. "
                                "Run ingestion and preprocessing pipelines first.")
    return pd.read_csv(data_path)

def prepare_model_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare data for the Bayesian model.
    Returns:
        y: outcome (judgment_rating)
        X_salience: salience predictor (0=low, 1=high)
        X_foundation: foundation score covariate
    """
    # Ensure columns exist
    required_cols = ['judgment_rating', 'salience_level', 'foundation_score']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    y = df['judgment_rating'].values.astype(float)
    
    # Map salience to numeric
    salience_map = {'low': 0, 'high': 1}
    if df['salience_level'].dtype == 'object':
        X_salience = df['salience_level'].map(salience_map).values.astype(float)
    else:
        X_salience = df['salience_level'].values.astype(float)
    
    X_foundation = df['foundation_score'].values.astype(float)
    
    return y, X_salience, X_foundation

def run_bayesian_model(y: np.ndarray, X_salience: np.ndarray, X_foundation: np.ndarray,
                       participant_id: str = "global", seed: int = 42) -> ModelResult:
    """
    Run the Bayesian decision model with convergence handling.
    
    If the model fails to converge (R-hat > 1.05), it falls back to MLE
    and flags the result as inconclusive.
    
    Args:
        y: Outcome variable (judgment ratings)
        X_salience: Binary salience predictor
        X_foundation: Foundation score covariate
        participant_id: Identifier for the result artifact
        seed: Random seed for reproducibility
    
    Returns:
        ModelResult artifact with posterior samples, R-hat, and fallback MLE if needed.
    """
    init_random_seeds(seed)
    n = len(y)
    
    # Define the model
    with pm.Model() as model:
        # Priors
        sigma = pm.HalfNormal('sigma', sigma=1.0)
        beta_salience = pm.Normal('beta_salience', mu=0, sigma=1.0)
        beta_foundation = pm.Normal('beta_foundation', mu=0, sigma=1.0)
        intercept = pm.Normal('intercept', mu=0, sigma=1.0)
        
        # Likelihood
        mu = intercept + beta_salience * X_salience + beta_foundation * X_foundation
        y_obs = pm.Normal('y_obs', mu=mu, sigma=sigma, observed=y)
        
        # Sampling
        # Use 1000 draws for speed in CI, 2 chains
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                trace = pm.sample(
                    draws=1000, 
                    tune=500, 
                    chains=2, 
                    target_accept=0.9,
                    return_inferencedata=True,
                    random_seed=seed
                )
            
            # Check convergence
            r_hat = az.rhat(trace).to_array().values.max()
            
            if r_hat > 1.05:
                logger.warning(f"Model failed to converge (R-hat={r_hat:.3f}). "
                               f"Triggering MLE fallback for participant {participant_id}.")
                raise ConvergenceError(f"R-hat {r_hat:.3f} exceeds threshold 1.05")
            
            # Extract posterior samples for the main effect of interest (beta_salience)
            posterior_samples = trace.posterior['beta_salience'].values.flatten().tolist()
            
            return ModelResult(
                participant_id=participant_id,
                posterior_samples=posterior_samples,
                r_hat=float(r_hat),
                is_inconclusive=False,
                mle_fallback=0.0  # Not needed if converged
            )
            
        except (ConvergenceError, Exception) as e:
            # Fallback to MLE
            logger.info(f"Falling back to MLE for participant {participant_id} due to: {e}")
            mle_beta, _ = fit_mle_model(y, X_salience, X_foundation)
            
            # Mark as inconclusive and report MLE
            return ModelResult(
                participant_id=participant_id,
                posterior_samples=[],  # No valid posterior
                r_hat=999.0,  # Sentinel for failure
                is_inconclusive=True,
                mle_fallback=float(mle_beta)
            )

def fit_mle_model(y: np.ndarray, X_salience: np.ndarray, X_foundation: np.ndarray) -> Tuple[float, float]:
    """
    Fit a simple linear regression as MLE fallback.
    Returns the coefficient for salience.
    """
    # Stack features
    X = np.column_stack([X_salience, X_foundation])
    model = LinearRegression()
    model.fit(X, y)
    
    # Return salience coefficient (index 0)
    return model.coef_[0], model.intercept_

class ConvergenceError(Exception):
    """Custom exception for convergence failures."""
    pass

def save_model_result(result: ModelResult, output_path: str):
    """
    Save the ModelResult to a JSON file.
    """
    data = result.to_dict()
    # Convert numpy types to native Python for JSON serialization
    for key, value in data.items():
        if isinstance(value, np.floating):
            data[key] = float(value)
        elif isinstance(value, np.integer):
            data[key] = int(value)
        elif isinstance(value, np.ndarray):
            data[key] = value.tolist()
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Model result saved to {output_path}")

def main():
    """
    Main entry point for Bayesian model execution.
    Loads preprocessed data, runs the model, and saves the result.
    """
    log_pipeline_step("Starting Bayesian Model Execution (T023)")
    
    try:
        # Load data
        df = load_preprocessed_data()
        logger.info(f"Loaded {len(df)} rows from preprocessed data.")
        
        # Prepare data
        y, X_salience, X_foundation = prepare_model_data(df)
        logger.info("Data prepared for Bayesian modeling.")
        
        # Run model
        # Use a generic ID for the global dataset run, or iterate if per-participant
        result = run_bayesian_model(y, X_salience, X_foundation, participant_id="pipeline_run")
        
        # Save result
        output_path = get_path("data/processed/model_result.json")
        save_model_result(result, output_path)
        
        # Validate schema
        if not validate_model_result_schema(result.to_dict()):
            raise ValueError("Generated result failed schema validation.")
        
        logger.info(f"Pipeline completed. Result: inconclusive={result.is_inconclusive}, "
                    f"r_hat={result.r_hat}, mle_fallback={result.mle_fallback:.4f}")
        
    except Exception as e:
        logger.error(f"Bayesian model execution failed: {e}")
        raise

if __name__ == "__main__":
    main()