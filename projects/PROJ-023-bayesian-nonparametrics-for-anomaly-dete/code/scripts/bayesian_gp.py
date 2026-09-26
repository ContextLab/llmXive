"""
Bayesian GP Anomaly Detection Script.

Implements Gaussian Process regression with Sparse Variational Inference (SVI)
using PyMC. This script loads processed time series data, fits a GP model with
inducing points, and outputs anomaly scores.

Architecture:
- Kernel: RBF (Squared Exponential)
- Inference: Sparse Variational Inference (SVI) with Adam optimizer
- Constraints: Fixed 1000 optimization steps, 7GB memory limit
- Convergence: ELBO stability check (relative change < 0.01 over last 50 steps)

Outputs:
- data/results/bayesian_predictions.csv: Anomaly scores and predictions
- data/results/memory_log.json: Memory profiling results
"""

import os
import sys
import logging
import time
import json
import tracemalloc
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List

import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from scipy.spatial.distance import cdist

# Project relative imports
# Note: Ensure code/ is in sys.path or run as module
from lib.memory_profiler import check_memory_limit, log_memory_usage
from lib.utils import set_seed, normalize_series

# Constants
MAX_STEPS = 1000
MEMORY_LIMIT_GB = 7.0
CONVERGENCE_WINDOW = 50
CONVERGENCE_THRESHOLD = 0.01
MAX_RETRIES = 3
RANDOM_SEED = 42

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/results/bayesian_gp.log")
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data(data_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load and validate processed time series data.

    Args:
        data_path: Path to the processed CSV file.

    Returns:
        Tuple of (time_values, series_values).
    """
    if not data_path.exists():
        logger.error(f"Processed data file not found: {data_path}")
        raise FileNotFoundError(f"Processed data file not found: {data_path}")

    df = pd.read_csv(data_path)

    # Validate required columns
    required_cols = ['timestamp', 'value']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns. Expected: {required_cols}, Found: {list(df.columns)}")

    # Handle missing values via interpolation (as per T008)
    df['value'] = df['value'].interpolate(method='linear').ffill().bfill()

    if df['value'].isna().any():
        logger.warning("Remaining NaN values after interpolation. Dropping rows.")
        df = df.dropna(subset=['value'])

    if len(df) < 10:
        raise ValueError("Insufficient data points for GP modeling.")

    # Normalize time to [0, 1] for numerical stability
    time_vals = df['timestamp'].values.astype(float)
    time_min, time_max = time_vals.min(), time_vals.max()
    if time_max > time_min:
        time_norm = (time_vals - time_min) / (time_max - time_min)
    else:
        time_norm = np.zeros_like(time_vals)

    series_vals = df['value'].values.astype(float)

    logger.info(f"Loaded {len(df)} data points. Time range: [{time_min}, {time_max}]")
    return time_norm, series_vals

def compute_elbo(model: pm.Model, trace: az.InferenceData) -> float:
    """
    Compute the Evidence Lower Bound (ELBO) from the trace.
    In PyMC SVI, this is typically available in the model log.
    For this implementation, we estimate stability from the trace's log_likelihood.
    """
    # In PyMC SVI, the ELBO is the objective function.
    # We approximate convergence by checking the stability of the model's log probability.
    # Since direct ELBO access might vary by backend, we use the sample stats if available.
    if hasattr(trace, 'sample_stats') and 'energy' in trace.sample_stats:
        energy = trace.sample_stats['energy'].values.flatten()
        # Lower energy generally indicates better fit in HMC, but for SVI we look at loss.
        # If using SVI specifically, we rely on the optimization history if stored.
        # Fallback: Use the last 50 log_likelihood values if available.
        pass

    # Fallback: Calculate negative log likelihood as a proxy for ELBO stability
    # This is a heuristic for convergence monitoring in this specific context.
    if hasattr(trace, 'posterior') and 'y_hat' in trace.posterior:
        # Simple proxy: variance of the posterior mean predictions
        y_hat = trace.posterior['y_hat'].mean(dim=['chain', 'draw'])
        return float(y_hat.var().item())

    return 0.0

def compute_ess(trace: az.InferenceData) -> float:
    """
    Compute Effective Sample Size (ESS) for key parameters.
    """
    if hasattr(trace, 'posterior'):
        ess = az.ess(trace)
        if isinstance(ess, az.InferenceData):
            # Average ESS across parameters
            return float(ess.mean().values.mean())
    return 0.0

def run_bayesian_gp(
    time_norm: np.ndarray,
    series_vals: np.ndarray,
    n_inducing: int = 20,
    n_steps: int = MAX_STEPS,
    seed: int = RANDOM_SEED
) -> Tuple[pd.DataFrame, bool, Dict[str, Any]]:
    """
    Run the Sparse Variational Inference Gaussian Process model.

    Args:
        time_norm: Normalized time values.
        series_vals: Observed series values.
        n_inducing: Number of inducing points.
        n_steps: Maximum optimization steps.
        seed: Random seed.

    Returns:
        Tuple of (predictions_df, convergence_status, metadata).
    """
    set_seed(seed)
    logger.info(f"Starting GP model with {n_inducing} inducing points, {n_steps} steps.")

    # Initialize inducing points
    np.random.seed(seed)
    inducing_idx = np.random.choice(len(time_norm), size=min(n_inducing, len(time_norm)), replace=False)
    Z = time_norm[inducing_idx].reshape(-1, 1)
    f_init = series_vals[inducing_idx]

    # Define the model
    coords = {"obs": range(len(time_norm))}
    with pm.Model(coords=coords) as gp_model:
        # Priors for kernel hyperparameters
        sigma = pm.HalfNormal("sigma", sigma=1.0)
        ls = pm.HalfNormal("ls", sigma=1.0)

        # Covariance function (RBF)
        cov_func = sigma**2 * pm.gp.cov.ExpQuad(1, ls=ls)

        # Sparse GP approximation
        gp = pm.gp.LatentSVI(cov_func=cov_func, Z=Z, f=f_init, M=10)  # M=10 mini-batches

        # Likelihood
        y = gp.prior("y", obs={"obs": time_norm.reshape(-1, 1)})

        # Variational Inference
        # Note: PyMC's SVI uses ADAM by default
        logger.info("Running Sparse Variational Inference...")

        # We need to track ELBO for convergence
        elbo_history = []
        approx = gp.fit(n=n_steps, progressbar=False, obj_optimizer=pm.adam(learning_rate=0.01))

        # Extract ELBO history if available (PyMC 5.0+ stores this in approx)
        if hasattr(approx, 'elbo'):
            elbo_history = approx.elbo
        else:
            # Fallback: run a small loop to track if possible, or assume convergence if steps completed
            # For robustness, we simulate a check based on the final state
            pass

        # Check convergence
        converged = False
        if len(elbo_history) >= CONVERGENCE_WINDOW:
            recent_elbo = elbo_history[-CONVERGENCE_WINDOW:]
            # Check relative change
            changes = np.diff(recent_elbo)
            avg_change = np.mean(np.abs(changes))
            if avg_change < CONVERGENCE_THRESHOLD * np.abs(np.mean(recent_elbo)):
                converged = True
                logger.info(f"Convergence detected: avg change {avg_change:.6f} < threshold {CONVERGENCE_THRESHOLD}")
            else:
                logger.warning(f"Convergence NOT detected: avg change {avg_change:.6f}")
        else:
            logger.warning(f"Insufficient ELBO history ({len(elbo_history)}) to check convergence.")

        # Sample from the posterior predictive
        logger.info("Generating posterior predictive samples...")
        # For SVI, we can use the approx distribution directly for predictions
        # or draw samples from the approximate posterior
        y_pred = gp.predict(time_norm.reshape(-1, 1), point=approx.sample(1000))

        # Calculate anomaly scores
        # Score = |observed - predicted_mean| / predicted_std
        mean_pred = y_pred.mean(axis=0)
        std_pred = y_pred.std(axis=0) + 1e-6  # Avoid division by zero
        anomaly_scores = np.abs(series_vals - mean_pred) / std_pred

        # Create output dataframe
        predictions_df = pd.DataFrame({
            'timestamp': time_norm, # Using normalized time for consistency
            'value': series_vals,
            'predicted_mean': mean_pred,
            'predicted_std': std_pred,
            'anomaly_score': anomaly_scores,
            'is_anomaly': (anomaly_scores > 3.0).astype(int) # Threshold heuristic
        })

        metadata = {
            'n_steps': n_steps,
            'converged': converged,
            'n_inducing': n_inducing,
            'final_elbo': elbo_history[-1] if elbo_history else None,
            'seed': seed
        }

    return predictions_df, converged, metadata

def main():
    """
    Main entry point for the Bayesian GP anomaly detection pipeline.
    """
    logger.info("Starting Bayesian GP Anomaly Detection (T016)")

    # Paths
    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "data" / "processed" / "series_with_anomalies.csv"
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "bayesian_predictions.csv"
    memory_log_path = output_dir / "memory_log.json"

    # Start memory profiling
    tracemalloc.start()
    start_time = time.time()

    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"Attempt {attempt}/{MAX_RETRIES}")
        try:
            # Load data
            time_norm, series_vals = load_processed_data(data_path)

            # Run model
            predictions_df, converged, metadata = run_bayesian_gp(time_norm, series_vals)

            # Check memory
            current, peak = tracemalloc.get_traced_memory()
            peak_gb = peak / (1024 ** 3)
            logger.info(f"Peak memory usage: {peak_gb:.2f} GB")

            if peak_gb > MEMORY_LIMIT_GB:
                logger.error(f"Memory limit exceeded: {peak_gb:.2f} GB > {MEMORY_LIMIT_GB} GB")
                raise MemoryError(f"Memory limit exceeded: {peak_gb:.2f} GB")

            # Log memory usage
            log_memory_usage(
                script_name="bayesian_gp.py",
                peak_memory_gb=peak_gb,
                output_path=memory_log_path
            )

            # Save results
            predictions_df.to_csv(output_path, index=False)
            logger.info(f"Predictions saved to {output_path}")

            # Save metadata
            metadata_path = output_dir / "bayesian_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Metadata saved to {metadata_path}")

            if not converged:
                logger.warning(f"Run {attempt} did not converge. Retrying...")
                continue

            # Success
            logger.info("Model converged and results saved successfully.")
            print(f"Success: {output_path}")
            return

        except MemoryError:
            logger.error("Memory error occurred. Stopping.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Attempt {attempt} failed: {str(e)}")
            if attempt == MAX_RETRIES:
                logger.error("Max retries reached. Failing.")
                sys.exit(1)
            # Exponential backoff or just retry immediately for now
            time.sleep(1)

    # Final fallback if loop exits without return
    logger.error("Unexpected exit from retry loop.")
    sys.exit(1)

if __name__ == "__main__":
    main()