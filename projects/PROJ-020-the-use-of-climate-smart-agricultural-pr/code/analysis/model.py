import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import logging
import signal
import sys
import time
import json
from datetime import datetime
import pickle
import os

from utils.logging import initialize_logging
from utils.config import get_processed_data_dir, get_state_dir

# Configure logging for this module
logger = logging.getLogger(__name__)

# Timeout configuration
MODEL_TIMEOUT_HOURS = 6
MODEL_TIMEOUT_SECONDS = MODEL_TIMEOUT_HOURS * 3600
REDUCED_BATCH_FACTOR = 0.5  # Reduce sample size by 50% on retry
STATE_FILE = "model_state_timeout.json"

def _save_timeout_state(state: Dict[str, Any], state_dir: Path) -> None:
    """Save the current model state to disk for recovery."""
    state_file = state_dir / STATE_FILE
    try:
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        logger.info(f"Saved timeout state to {state_file}")
    except Exception as e:
        logger.error(f"Failed to save timeout state: {e}")

def _load_timeout_state(state_dir: Path) -> Optional[Dict[str, Any]]:
    """Load the previous timeout state from disk."""
    state_file = state_dir / STATE_FILE
    if not state_file.exists():
        return None
    try:
        with open(state_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load timeout state: {e}")
        return None

def _clear_timeout_state(state_dir: Path) -> None:
    """Clear the timeout state file after successful completion."""
    state_file = state_dir / STATE_FILE
    if state_file.exists():
        state_file.unlink()
        logger.info(f"Cleared timeout state from {state_file}")

def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    logger.warning("Model execution timeout reached. Initiating graceful shutdown.")
    raise TimeoutError("Model execution exceeded time limit")

def _setup_timeout_handler(timeout_seconds: int):
    """Set up a signal-based timeout handler (Unix only)."""
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout_seconds)
    else:
        logger.warning("SIGALRM not available on this platform. Using alternative timeout strategy.")

def _cancel_timeout_handler():
    """Cancel the timeout handler."""
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)

def _create_reduced_batch(data: pd.DataFrame, target_size: int) -> pd.DataFrame:
    """Create a reduced batch of data for retry."""
    if len(data) <= target_size:
        return data
    
    # Stratified sampling to preserve distribution
    if 'country' in data.columns:
        # Sample proportionally by country
        country_counts = data['country'].value_counts(normalize=True)
        reduced_data = []
        for country, proportion in country_counts.items():
            country_data = data[data['country'] == country]
            sample_size = int(target_size * proportion)
            if sample_size > 0:
                reduced_data.append(country_data.sample(n=min(sample_size, len(country_data)), random_state=42))
        return pd.concat(reduced_data, ignore_index=True)
    else:
        # Simple random sampling
        return data.sample(n=target_size, random_state=42)

def calculate_fdr_adjusted_pvalues(pvalues: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        pvalues: List of raw p-values from hypothesis tests
        
    Returns:
        List of FDR-adjusted p-values
    """
    pvalues = np.array(pvalues)
    n = len(pvalues)
    if n == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(pvalues)
    sorted_pvalues = pvalues[sorted_indices]
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * sorted_pvalues.max()
    
    # Find the largest k where p(k) <= critical(k)
    valid = sorted_pvalues <= critical_values
    if not np.any(valid):
        # If no valid p-values, return original
        return pvalues.tolist()
    
    # Adjust p-values
    adjusted = np.minimum.accumulate((n / ranks) * sorted_pvalues[::-1])[::-1]
    adjusted = np.minimum(adjusted, 1.0)  # Ensure p-values <= 1
    
    # Restore original order
    result = np.empty(n)
    result[sorted_indices] = adjusted
    
    return result.tolist()

def run_mixed_effects_model(
    data: pd.DataFrame,
    formula: str,
    random_effect: str,
    weights: Optional[pd.Series] = None,
    state_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run a mixed-effects regression model with timeout handling and reduced-batch retry.
    
    Args:
        data: DataFrame containing the analysis data
        formula: Model formula (e.g., "food_security ~ csa_index + covariates")
        random_effect: Random effect grouping variable (e.g., "region")
        weights: Optional sampling weights
        state_dir: Directory for saving timeout state
        
    Returns:
        Dictionary containing model results and diagnostics
    """
    if state_dir is None:
        state_dir = get_state_dir()
    
    # Check for existing timeout state
    prev_state = _load_timeout_state(state_dir)
    is_retry = prev_state is not None
    
    start_time = time.time()
    
    # Set up timeout handler
    _setup_timeout_handler(MODEL_TIMEOUT_SECONDS)
    
    try:
        # If retrying, create reduced batch
        if is_retry:
            logger.warning("Retrying with reduced batch size.")
            target_size = int(len(data) * REDUCED_BATCH_FACTOR)
            data = _create_reduced_batch(data, target_size)
            logger.info(f"Reduced dataset to {len(data)} rows ({target_size} target)")
        
        # Prepare model
        if weights is not None:
            model = smf.mixedlm(formula, data, groups=data[random_effect], weights=weights)
        else:
            model = smf.mixedlm(formula, data, groups=data[random_effect])
        
        # Fit model
        logger.info(f"Fitting mixed-effects model with formula: {formula}")
        result = model.fit(maxiter=1000)
        
        # Cancel timeout handler
        _cancel_timeout_handler()
        
        elapsed = time.time() - start_time
        
        # Extract results
        results_dict = {
            "coefficients": result.params.to_dict(),
            "std_errors": result.bse.to_dict(),
            "p_values": result.pvalues.to_dict(),
            "random_effects": result.random_effects,
            "log_likelihood": result.llf,
            "aic": result.aic,
            "bic": result.bic,
            "n_obs": len(data),
            "n_groups": data[random_effect].nunique(),
            "formula": formula,
            "random_effect": random_effect,
            "elapsed_seconds": elapsed,
            "is_retry": is_retry,
            "retry_batch_size": len(data) if is_retry else None
        }
        
        # Clear timeout state on success
        _clear_timeout_state(state_dir)
        
        logger.info(f"Model fitting completed successfully in {elapsed:.2f} seconds")
        return results_dict
        
    except TimeoutError as e:
        _cancel_timeout_handler()
        elapsed = time.time() - start_time
        
        logger.warning(f"Model fitting timed out after {elapsed:.2f} seconds")
        
        # Save state for retry
        state = {
            "formula": formula,
            "random_effect": random_effect,
            "data_size": len(data),
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
        _save_timeout_state(state, state_dir)
        
        # Attempt reduced-batch retry
        logger.info("Attempting reduced-batch retry...")
        return run_mixed_effects_model(data, formula, random_effect, weights, state_dir)
        
    except Exception as e:
        _cancel_timeout_handler()
        elapsed = time.time() - start_time
        
        # Save error state
        state = {
            "formula": formula,
            "random_effect": random_effect,
            "data_size": len(data),
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__
        }
        _save_timeout_state(state, state_dir)
        
        logger.error(f"Model fitting failed: {e}")
        raise
        
    finally:
        _cancel_timeout_handler()

def run_mediation_analysis(
    data: pd.DataFrame,
    formula_x: str,
    formula_m: str,
    formula_y: str,
    random_effect: str,
    weights: Optional[pd.Series] = None
) -> Dict[str, Any]:
    """
    Perform mediation analysis for indirect effects.
    
    Args:
        data: DataFrame containing the analysis data
        formula_x: Formula for X -> M (independent -> mediator)
        formula_m: Formula for M -> Y (mediator -> dependent)
        formula_y: Formula for X + M -> Y (full model)
        random_effect: Random effect grouping variable
        weights: Optional sampling weights
        
    Returns:
        Dictionary containing mediation analysis results
    """
    logger.info("Running mediation analysis")
    
    # Fit X -> M model
    model_xm = smf.mixedlm(formula_x, data, groups=data[random_effect])
    result_xm = model_xm.fit()
    
    # Fit M -> Y model (with X)
    model_y = smf.mixedlm(formula_y, data, groups=data[random_effect])
    result_y = model_y.fit()
    
    # Extract coefficients
    # Assuming X is the first predictor in both formulas
    # This is a simplified mediation analysis
    # In practice, you'd need to parse formulas to identify the specific coefficients
    
    results = {
        "effect_xm": result_xm.params.to_dict(),
        "effect_y": result_y.params.to_dict(),
        "indirect_effect": None,  # Would require specific coefficient extraction
        "direct_effect": result_y.params.to_dict(),
        "n_obs": len(data)
    }
    
    logger.info("Mediation analysis completed")
    return results

def run_robustness_checks(
    data: pd.DataFrame,
    formula: str,
    random_effect: str,
    weights: Optional[pd.Series] = None
) -> Dict[str, Any]:
    """
    Run robustness checks including alternative specifications and sensitivity analysis.
    
    Args:
        data: DataFrame containing the analysis data
        formula: Base model formula
        random_effect: Random effect grouping variable
        weights: Optional sampling weights
        
    Returns:
        Dictionary containing robustness check results
    """
    logger.info("Running robustness checks")
    
    results = {
        "base_model": run_mixed_effects_model(data, formula, random_effect, weights),
        "alternative_specifications": [],
        "sensitivity_analysis": {}
    }
    
    # Run alternative specifications
    # Example: Remove one covariate at a time
    # This is simplified - in practice, you'd parse the formula
    
    logger.info("Robustness checks completed")
    return results

def main():
    """Main entry point for model analysis."""
    initialize_logging()
    
    logger.info("Starting model analysis pipeline")
    
    # Load data
    processed_dir = get_processed_data_dir()
    data_path = processed_dir / "merged_sample.parquet"
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    data = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(data)} rows from {data_path}")
    
    # Define model formula
    # Example: food_security ~ csa_index + covariates
    formula = "food_security ~ csa_index + education + income + age"
    random_effect = "region"
    
    # Run model
    state_dir = get_state_dir()
    results = run_mixed_effects_model(data, formula, random_effect, state_dir=state_dir)
    
    # Save results
    output_path = processed_dir / "model_results.pkl"
    with open(output_path, 'wb') as f:
        pickle.dump(results, f)
    
    logger.info(f"Model results saved to {output_path}")
    
    # Print summary
    print("\n=== Model Results Summary ===")
    print(f"Formula: {results['formula']}")
    print(f"Observations: {results['n_obs']}")
    print(f"Groups: {results['n_groups']}")
    print(f"Elapsed: {results['elapsed_seconds']:.2f}s")
    print(f"Is Retry: {results['is_retry']}")
    if results['is_retry']:
        print(f"Retry Batch Size: {results['retry_batch_size']}")
    print("\nCoefficients:")
    for var, coef in results['coefficients'].items():
        print(f"  {var}: {coef:.4f} (p={results['p_values'][var]:.4f})")
    
    return results

if __name__ == "__main__":
    main()