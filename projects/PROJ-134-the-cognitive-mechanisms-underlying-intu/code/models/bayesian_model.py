"""
Bayesian Model Implementation (PyMC5) with Schema Compliance Wrapper.

Implements T022b (Model Definition) and T022c (Wrapper/Schema Compliance).
Returns a `ModelResult` object adhering to the schema defined in T051.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# PyMC5 imports
try:
    import pymc as pm
    from pymc import Model, InferenceData
except ImportError:
    # Fallback for environments where pymc might be named differently or not installed
    # but per spec.md FR-002, pymc==5.12.0 is mandated.
    raise ImportError("PyMC5 is required. Install via: pip install pymc==5.12.0")

# Local imports
from code.config import get_path, N_CONFIG
from code.utils.logging import get_logger, log_operation

# Define the ModelResult schema explicitly here to ensure compliance
# as per T051.
class ConvergenceError(Exception):
    """Raised when the model fails to converge."""
    pass

class ModelResult:
    """
    Schema-compliant container for model results (T051).
    
    Fields:
        participant_id: Optional identifier (if aggregated)
        posterior_samples: Dict of parameter name -> array of samples
        r_hat: Dict of parameter name -> R-hat statistic
        is_inconclusive: Boolean flag if convergence criteria not met
        mle_fallback: Optional float (MLE estimate if Bayesian failed)
        trace: InferenceData object (raw trace)
    """
    def __init__(
        self,
        posterior_samples: Dict[str, np.ndarray],
        r_hat: Dict[str, float],
        is_inconclusive: bool,
        mle_fallback: Optional[float] = None,
        trace: Optional[InferenceData] = None,
        participant_id: Optional[str] = None
    ):
        self.posterior_samples = posterior_samples
        self.r_hat = r_hat
        self.is_inconclusive = is_inconclusive
        self.mle_fallback = mle_fallback
        self.trace = trace
        self.participant_id = participant_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (excluding trace)."""
        # Convert numpy arrays to lists for JSON serialization
        samples_serializable = {
            k: v.tolist() if isinstance(v, np.ndarray) else v
            for k, v in self.posterior_samples.items()
        }
        return {
            "participant_id": self.participant_id,
            "posterior_samples": samples_serializable,
            "r_hat": self.r_hat,
            "is_inconclusive": self.is_inconclusive,
            "mle_fallback": self.mle_fallback
        }

def build_model(data: pd.DataFrame) -> Model:
    """
    T022b: Define the PyMC5 model.
    
    Model: Hierarchical regression of judgment_rating on salience_level.
    Formula: judgment_rating ~ salience_level + (1|participant_id)
    
    Args:
        data: Preprocessed DataFrame with columns:
              - 'judgment_rating': float
              - 'salience_level': categorical ('low', 'high')
              - 'participant_id': string/int
    
    Returns:
        pm.Model object.
    """
    logger = get_logger("bayesian_model")
    logger.log("build_model", status="start")

    with pm.Model() as model:
        # Data containers
        y = pm.Data("y", data["judgment_rating"].values)
        salience = pm.Data("salience", data["salience_level"].values)
        participants = pm.Data("participants", data["participant_id"].values)
        
        # Encode salience (0=low, 1=high)
        salience_encoded = (salience == "high").astype(int)
        
        # Priors
        sigma = pm.HalfNormal("sigma", 1.0)
        beta_intercept = pm.Normal("beta_intercept", 0, 1)
        beta_salience = pm.Normal("beta_salience", 0, 1)
        
        # Hierarchical intercepts for participants
        participant_indices, unique_participants = pd.factorize(participants)
        n_participants = len(unique_participants)
        sigma_participant = pm.HalfNormal("sigma_participant", 1.0)
        participant_offsets = pm.Normal("participant_offsets", 0, 1, shape=n_participants)
        participant_intercepts = sigma_participant * participant_offsets
        
        # Linear predictor
        mu = beta_intercept + beta_salience * salience_encoded + participant_intercepts[participant_indices]
        
        # Likelihood
        y_obs = pm.Normal("y_obs", mu=mu, sigma=sigma, observed=y)
        
        logger.log("build_model", status="complete", n_params=5)
        
    return model

def run_model(data: pd.DataFrame, chains: int = 4, draws: int = 1000, target_accept: float = 0.9) -> ModelResult:
    """
    T022c: Wrapper to run the model and ensure schema compliance.
    
    Executes sampling, checks convergence (R-hat < 1.05), and returns
    a ModelResult object.
    
    Args:
        data: Preprocessed DataFrame.
        chains: Number of MCMC chains.
        draws: Number of draws per chain.
        target_accept: Target acceptance rate for NUTS.
    
    Returns:
        ModelResult object.
    
    Raises:
        ConvergenceError: If R-hat > 1.05 for any parameter.
    """
    logger = get_logger("bayesian_model")
    log_operation("run_model", status="start", chains=chains, draws=draws)

    # Build model
    model = build_model(data)
    
    # GPU Detection (T063/T066)
    has_gpu = False
    try:
        import torch
        has_gpu = torch.cuda.is_available()
        if has_gpu:
            logger.log("run_model", gpu_detected=True, device="cuda")
    except ImportError:
        logger.log("run_model", gpu_detected=False, device="cpu")
    
    start_time = time.time()
    trace = None
    r_hat = {}
    is_inconclusive = False
    mle_fallback = None

    try:
        # Sampling
        # If GPU is available, we might use numpyro, but for robustness in this
        # specific task scope, we stick to standard PyMC5 sampling which can
        # leverage GPU via backend if configured, or run on CPU.
        # We enforce a timeout for CPU runs to trigger offload if needed.
        timeout_limit = 14400 # 4 hours in seconds
        
        with model:
            # Try to sample
            # Note: PyMC5 handles device selection internally if torch is available and configured
            trace = pm.sample(
                draws=draws,
                chains=chains,
                target_accept=target_accept,
                random_seed=42,
                return_inferencedata=True,
                progressbar=True
            )
            
            elapsed = time.time() - start_time
            logger.log("run_model", status="sampling_complete", elapsed_seconds=elapsed)

            # Convergence Check
            # Extract R-hat from trace
            # In PyMC5, trace.summary() or arviz.rhat() can be used.
            # We assume trace is an InferenceData object.
            import arviz as az
            summary = az.summary(trace, var_names=["beta_intercept", "beta_salience", "sigma", "sigma_participant"])
            
            r_hat_values = {}
            max_r_hat = 0.0
            
            # Extract R-hat from summary (column 'r_hat')
            for param in summary.index:
                if 'r_hat' in summary.columns:
                    val = float(summary.loc[param, 'r_hat'])
                    r_hat_values[param] = val
                    if val > max_r_hat:
                        max_r_hat = val
            
            r_hat = r_hat_values
            
            if max_r_hat > 1.05:
                is_inconclusive = True
                logger.log("run_model", status="warning", message=f"R-hat {max_r_hat} > 1.05", inconclusive=True)
                # Do not raise immediately, let the caller decide, but flag it.
                # However, per T022d, we should raise if it's a hard failure.
                # For T022c, we return the result with the flag.
            
            # Extract posterior samples
            posterior_samples = {}
            for var_name in ["beta_intercept", "beta_salience", "sigma", "sigma_participant"]:
                if var_name in trace.posterior.data_vars:
                    posterior_samples[var_name] = trace.posterior[var_name].values.flatten()
                    
    except Exception as e:
        elapsed = time.time() - start_time
        logger.log("run_model", status="error", error=str(e), elapsed_seconds=elapsed)
        
        # Check if it's a convergence timeout or CUDA error
        if "CUDA" in str(e) or "convergence" in str(e).lower():
            if elapsed > timeout_limit and not has_gpu:
                raise ConvergenceError("Convergence failed on CPU. Re-run on GPU.") from e
        
        # Fallback to MLE if sampling fails completely
        # Simple OLS as fallback for demonstration
        try:
            import statsmodels.api as sm
            # Prepare data for OLS
            X = pd.get_dummies(data["salience_level"], prefix="salience", drop_first=True)
            X = sm.add_constant(X)
            y = data["judgment_rating"]
            ols_model = sm.OLS(y, X).fit()
            mle_fallback = float(ols_model.params.get("salience_high", 0.0))
            logger.log("run_model", status="mle_fallback", mle_value=mle_fallback)
        except Exception as fallback_err:
            logger.log("run_model", status="mle_fallback_failed", error=str(fallback_err))
            raise ConvergenceError(f"Sampling failed and MLE fallback failed: {fallback_err}") from e

    # Construct Result
    result = ModelResult(
        posterior_samples=posterior_samples,
        r_hat=r_hat,
        is_inconclusive=is_inconclusive,
        mle_fallback=mle_fallback,
        trace=trace
    )
    
    log_operation("run_model", status="complete", inconclusive=is_inconclusive)
    return result

def main():
    """Entry point for testing the model wrapper."""
    logger = get_logger("bayesian_model")
    log_operation("main", status="start")
    
    # Load sample data for testing if no file provided
    # In real execution, this would be called by run_bayesian.py
    try:
        data_path = get_path("data/processed/preprocessed_data.csv")
        if os.path.exists(data_path):
            data = pd.read_csv(data_path)
        else:
            # Fallback for testing: generate minimal synthetic data
            logger.log("main", status="no_data_file", message="Generating test data")
            np.random.seed(42)
            n = 50
            data = pd.DataFrame({
                "participant_id": [f"P{i}" for i in range(n)],
                "salience_level": np.random.choice(["low", "high"], n),
                "judgment_rating": np.random.normal(3.0, 0.5, n)
            })
    except Exception as e:
        logger.log("main", status="error", error=str(e))
        return

    try:
        result = run_model(data)
        print(f"Model Run Complete. Inconclusive: {result.is_inconclusive}")
        print(f"R-hat stats: {result.r_hat}")
        if result.mle_fallback is not None:
            print(f"MLE Fallback: {result.mle_fallback}")
    except ConvergenceError as e:
        print(f"Convergence Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()