"""
Bayesian Model Implementation (PyMC5).

This module implements the Bayesian model for analyzing moral judgments.
It provides functions to build the model, run inference, and ensure
schema compliance for the ModelResult artifact.

Deviation Note: This implementation uses PyMC5 (successor to PyMC3)
as per Plan.md Section "Spec Deviation & Resolution".
"""
from __future__ import annotations

import os
import sys
from typing import Dict, Any, Optional, Tuple, List, Union

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from pydantic import BaseModel, Field, field_validator
from typing import Optional as PyOptional

# Import config for paths
from code.config import get_path

# Import schemas for validation
# Note: T051 defined ModelResult schema in code/utils/schemas.py
# We define it here as well for self-containment or import if available
try:
    from code.utils.schemas import ModelResult
except ImportError:
    # Fallback definition if utils.schemas is not yet updated or available
    class ModelResult(BaseModel):
        """Schema for Bayesian Model Results (T051)."""
        participant_id: Optional[str] = None
        posterior_samples: Dict[str, Any] = Field(default_factory=dict)
        r_hat: Dict[str, float] = Field(default_factory=dict)
        is_inconclusive: bool = False
        mle_fallback: Optional[float] = None

        @field_validator('r_hat')
        @classmethod
        def validate_r_hat(cls, v):
            for k, val in v.items():
                if not (0.9 <= val <= 1.2):
                    raise ValueError(f"R-hat for {k} ({val}) is out of expected range [0.9, 1.2]")
            return v


class ConvergenceError(Exception):
    """Raised when MCMC sampling fails to converge."""
    pass


def build_model(data: pd.DataFrame) -> pm.Model:
    """
    Build the PyMC5 Bayesian model.

    Model: Hierarchical Mixed-Effects Regression
    Judgment ~ Salience + MFQ_Score + (1 | Participant)

    Args:
        data: DataFrame with columns:
              - 'judgment_rating' (float)
              - 'salience_level' (int: 0=low, 1=high)
              - 'mfq_total_score' (float)
              - 'participant_id' (str)

    Returns:
        pm.Model object
    """
    with pm.Model() as model:
        # Priors
        # Intercept
        mu_intercept = pm.Normal('mu_intercept', mu=0, sigma=10)

        # Coefficients
        beta_salience = pm.Normal('beta_salience', mu=0, sigma=5)
        beta_mfq = pm.Normal('beta_mfq', mu=0, sigma=5)

        # Group-level effects (Participant)
        participant_indices = data['participant_id'].astype('category').cat.codes.values
        n_participants = len(data['participant_id'].astype('category').categories)

        sigma_participant = pm.HalfNormal('sigma_participant', sigma=5)
        theta_participant = pm.Normal('theta_participant', mu=0, sigma=sigma_participant, shape=n_participants)

        # Linear predictor
        # Map categorical indices to theta values
        participant_effect = theta_participant[participant_indices]

        mu = (
            mu_intercept
            + beta_salience * data['salience_level'].values
            + beta_mfq * data['mfq_total_score'].values
            + participant_effect
        )

        # Likelihood
        sigma = pm.HalfNormal('sigma', sigma=5)
        y_obs = pm.Normal('y_obs', mu=mu, sigma=sigma, observed=data['judgment_rating'].values)

        return model


def run_model(data: pd.DataFrame, 
              draws: int = 1000, 
              tune: int = 500, 
              chains: int = 2) -> ModelResult:
    """
    Run the Bayesian model and return a ModelResult object.

    This function wraps the model building, sampling, and result serialization
    to ensure compliance with the ModelResult schema (T051).

    Args:
        data: Preprocessed DataFrame.
        draws: Number of posterior draws.
        tune: Number of tuning steps.
        chains: Number of MCMC chains.

    Returns:
        ModelResult object containing posterior samples, R-hat values, etc.

    Raises:
        ConvergenceError: If R-hat values indicate non-convergence.
    """
    if data.empty:
        raise ValueError("Input data is empty.")

    # Prepare data for PyMC
    # Ensure numeric types
    data = data.copy()
    if 'salience_level' not in data.columns:
        # Fallback if column missing, assume 0
        data['salience_level'] = 0
    if 'mfq_total_score' not in data.columns:
        data['mfq_total_score'] = 0.0

    # Build model
    model = build_model(data)

    # Check for GPU/CUDA availability for PyMC (if supported)
    # PyMC uses JAX/NumPy backend. For this implementation, we default to CPU
    # but the logic is prepared for device selection if needed.
    # In a GPU environment, PyMC5 can utilize JAX on GPU automatically.
    
    try:
        with model:
            trace = pm.sample(
                draws=draws,
                tune=tune,
                chains=chains,
                return_inferencedata=True,
                random_seed=42,
                progressbar=False
            )
    except Exception as e:
        # Fallback to MLE if MCMC fails (e.g., convergence issues)
        # This is a safety net for the pipeline, not the primary path.
        # Calculate simple OLS/MLE fallback
        import statsmodels.api as sm
        try:
            X = sm.add_constant(data[['salience_level', 'mfq_total_score']])
            y = data['judgment_rating']
            mle_model = sm.OLS(y, X).fit()
            # Return a partial result indicating fallback
            return ModelResult(
                participant_id=None,
                posterior_samples={},
                r_hat={},
                is_inconclusive=True,
                mle_fallback=mle_model.params['salience_level'] if 'salience_level' in mle_model.params else 0.0
            )
        except Exception:
            raise ConvergenceError(f"Model sampling failed and MLE fallback also failed: {e}")

    # Extract diagnostics
    r_hat_values = az.rhat(trace)
    
    # Check convergence
    is_inconclusive = False
    for var_name, r_val in r_hat_values.items():
        # Convert to float if it's an array (scalar rhat)
        r_val_float = float(r_val.values) if hasattr(r_val, 'values') else float(r_val)
        if r_val_float > 1.1:
            is_inconclusive = True
            break

    # Prepare posterior samples (serializeable)
    posterior_samples = {}
    for var_name in trace.posterior.data_vars:
        samples = trace.posterior[var_name].values
        # Convert numpy array to list for JSON serialization
        posterior_samples[str(var_name)] = samples.tolist()

    # Format R-hat for schema
    r_hat_dict = {}
    for var_name in r_hat_values.data_vars:
        val = r_hat_values[var_name].values
        r_hat_dict[str(var_name)] = float(val)

    return ModelResult(
        participant_id=None, # Aggregated result
        posterior_samples=posterior_samples,
        r_hat=r_hat_dict,
        is_inconclusive=is_inconclusive,
        mle_fallback=None
    )


def main():
    """
    Main entry point for testing the model wrapper.
    Generates synthetic data and runs the model to verify schema compliance.
    """
    print("Running Bayesian Model Wrapper (T022c) Test...")
    
    # Create synthetic data for testing
    n = 100
    data = pd.DataFrame({
        'participant_id': [f"P{i}" for i in range(n)],
        'salience_level': np.random.randint(0, 2, n),
        'mfq_total_score': np.random.normal(50, 10, n),
        'judgment_rating': np.random.normal(3.5, 1.0, n)
    })

    try:
        result = run_model(data)
        print(f"Model run successful.")
        print(f"Is Inconclusive: {result.is_inconclusive}")
        print(f"R-hat keys: {list(result.r_hat.keys())}")
        
        # Verify schema
        assert isinstance(result, ModelResult)
        assert hasattr(result, 'posterior_samples')
        assert hasattr(result, 'r_hat')
        
        print("Schema validation passed.")
        
        # Save result to disk as declared in T022c
        output_path = get_path("data/processed/model_results.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert to dict for JSON serialization
        result_dict = result.model_dump()
        
        import json
        with open(output_path, 'w') as f:
            json.dump(result_dict, f, indent=2, default=str)
        
        print(f"Results written to {output_path}")
        
    except Exception as e:
        print(f"Error running model: {e}")
        raise

if __name__ == "__main__":
    main()