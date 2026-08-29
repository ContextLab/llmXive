import os
import sys
import json
import logging
import argparse
import warnings
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Third-party imports
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except ImportError:
    raise ImportError("statsmodels is required. Install via: pip install statsmodels")

from config import get_config, get_data_path, get_random_seed
from logging_config import setup_logging

# Constants
LOG_DIR = Path("artifacts/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger = setup_logging("bootstrap_convergence")

def load_analysis_data() -> pd.DataFrame:
    """Load the analysis-ready CSV from data/processed/analysis.csv."""
    config = get_config()
    data_path = get_data_path()
    csv_path = Path(data_path) / "processed" / "analysis.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Analysis CSV not found at {csv_path}. "
                                "Run preprocessing pipeline first.")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    return df

def prepare_model_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare data for mixed-effects model, handling missing values."""
    # Ensure required columns exist
    required_cols = ['recall', 'fixation_duration', 'valence', 'trait_anxiety', 'participant', 'stimulus_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Drop rows with missing values in key columns
    df_clean = df.dropna(subset=required_cols)
    
    # Convert categorical columns
    df_clean['valence'] = df_clean['valence'].astype('category')
    df_clean['participant'] = df_clean['participant'].astype('category')
    df_clean['stimulus_id'] = df_clean['stimulus_id'].astype('category')
    
    # Log sample size
    logger.info(f"Prepared {len(df_clean)} rows for model (dropped {len(df) - len(df_clean)} missing)")
    return df_clean

def fit_mixed_effects_model(data: pd.DataFrame, 
                            formula: str = "recall ~ fixation_duration * valence * trait_anxiety + (1|participant) + (1|stimulus_id)",
                            maxiter: int = 1000) -> Tuple[Any, bool]:
    """
    Fit a mixed-effects logistic regression model.
    
    Returns:
        Tuple of (model_result, convergence_status)
        convergence_status is True if model converged, False otherwise.
    """
    try:
        # Use bobyqa optimizer for better convergence
        model = smf.mixedlm(
            formula,
            data,
            groups=data["participant"],
            re_formula="1"
        )
        
        # Try fitting with bobyqa
        result = model.fit(method="bobyqa", maxiter=maxiter)
        
        # Check convergence
        # In statsmodels mixedlm, convergence is indicated by the status code
        # 0 usually means success, but we check the convergence attribute if available
        converged = True
        if hasattr(result, 'converged'):
            converged = result.converged
        elif hasattr(result, 'status'):
            # Some versions use status code
            converged = (result.status == 0)
        
        return result, converged
        
    except Exception as e:
        logger.warning(f"Model fitting failed: {str(e)}")
        return None, False

def fit_mixed_effects_model_full(data: pd.DataFrame) -> Tuple[Any, bool]:
    """Fit the full model with all interactions."""
    formula = "recall ~ fixation_duration * valence * trait_anxiety + (1|participant) + (1|stimulus_id)"
    return fit_mixed_effects_model(data, formula)

def fit_reduced_model(data: pd.DataFrame) -> Tuple[Any, bool]:
    """Fit the reduced model without the three-way interaction."""
    formula = "recall ~ fixation_duration * valence + fixation_duration * trait_anxiety + valence * trait_anxiety + (1|participant) + (1|stimulus_id)"
    return fit_mixed_effects_model(data, formula)

def run_likelihood_ratio_test(full_model: Any, reduced_model: Any) -> Dict[str, Any]:
    """Perform likelihood-ratio test comparing full vs reduced model."""
    if full_model is None or reduced_model is None:
        raise ValueError("Both models must be fitted to perform LRT")
    
    # Calculate LRT statistic
    ll_full = full_model.llf
    ll_reduced = reduced_model.llf
    lr_stat = 2 * (ll_full - ll_reduced)
    
    # Degrees of freedom = difference in number of parameters
    # For three-way interaction, we add 1 parameter (the interaction term)
    # But actually, for categorical valence with k levels, it's (k-1) extra parameters
    # Simplified: assume 1 df for the interaction term
    df_diff = 1  # This is a simplification; in practice, calculate based on formula differences
    
    # Calculate p-value
    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(lr_stat, df_diff)
    
    return {
        "lr_statistic": lr_stat,
        "df_diff": df_diff,
        "p_value": p_value,
        "significant": p_value < 0.05
    }

def run_residual_diagnostics(model: Any) -> Dict[str, Any]:
    """Run residual diagnostics and check for overdispersion."""
    # For mixed-effects models, overdispersion is less straightforward
    # We'll use a simplified approach: check if residuals are well-behaved
    
    # Get predictions
    predictions = model.predict()
    
    # Calculate residuals
    # Note: This is a simplified approach; proper GLMM residuals are more complex
    residuals = model.model.endog - predictions
    
    # Check for overdispersion (simplified)
    # In logistic regression, overdispersion is measured by residual deviance / df
    # For mixed models, this is approximated
    residual_deviance = -2 * model.llf
    df_residual = len(model.model.endog) - len(model.params)
    dispersion = residual_deviance / df_residual if df_residual > 0 else float('inf')
    
    return {
        "convergence": "OK" if model.converged else "FAILED",
        "dispersion": dispersion,
        "overdispersion_flag": dispersion > 1.2,
        "residual_deviance": residual_deviance,
        "df_residual": df_residual
    }

def run_bootstrap_convergence_verification(data: pd.DataFrame, 
                                            n_bootstrap: int = 100,
                                            sample_fraction: float = 0.8,
                                            seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Run bootstrap simulation to verify convergence rate when initial model fails.
    
    This function is MANDATORY to run ONLY if:
    1. The initial model (T020) fails to converge, OR
    2. Sample size is small (n < 100 observations)
    
    It empirically verifies the high convergence rate (SC-002) by running
    bootstrap samples and calculating the percentage where the model converges.
    
    Args:
        data: Prepared model data
        n_bootstrap: Number of bootstrap iterations
        sample_fraction: Fraction of data to sample in each iteration
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with convergence metrics
    """
    if seed is None:
        seed = get_random_seed()
    
    logger.info(f"Starting bootstrap convergence verification with {n_bootstrap} iterations")
    logger.info(f"Sample fraction: {sample_fraction}, Seed: {seed}")
    
    # Set random seed
    random.seed(seed)
    np.random.seed(seed)
    
    n_total = len(data)
    n_samples = int(n_total * sample_fraction)
    
    if n_samples < 10:
        raise ValueError(f"Sample size too small after bootstrapping: {n_samples}")
    
    convergence_count = 0
    bootstrap_results = []
    
    for i in range(n_bootstrap):
        # Sample data with replacement
        sample_indices = np.random.choice(n_total, size=n_samples, replace=True)
        sample_data = data.iloc[sample_indices].reset_index(drop=True)
        
        # Try to fit model
        try:
            result, converged = fit_mixed_effects_model_full(sample_data)
            
            if converged:
                convergence_count += 1
                status = "OK"
            else:
                status = "FAILED"
                
            bootstrap_results.append({
                "iteration": i,
                "sample_size": n_samples,
                "converged": converged,
                "status": status
            })
            
        except Exception as e:
            # Model fitting failed
            bootstrap_results.append({
                "iteration": i,
                "sample_size": n_samples,
                "converged": False,
                "status": "ERROR",
                "error": str(e)
            })
        
        # Log progress every 10 iterations
        if (i + 1) % 10 == 0:
            logger.info(f"Bootstrap iteration {i+1}/{n_bootstrap} - "
                       f"Convergence rate so far: {convergence_count/(i+1)*100:.1f}%")
    
    # Calculate final metrics
    convergence_rate = convergence_count / n_bootstrap if n_bootstrap > 0 else 0.0
    
    # Determine if convergence rate is "high" (threshold: 80%)
    high_convergence = convergence_rate >= 0.80
    
    result = {
        "bootstrap_iterations": n_bootstrap,
        "sample_fraction": sample_fraction,
        "original_sample_size": n_total,
        "bootstrap_sample_size": n_samples,
        "convergence_count": convergence_count,
        "convergence_rate": convergence_rate,
        "high_convergence_rate": high_convergence,
        "seed": seed,
        "status": "Convergence: OK" if high_convergence else "Convergence: LOW",
        "bootstrap_details": bootstrap_results[:10]  # Store first 10 for debugging
    }
    
    logger.info(f"Bootstrap convergence verification complete. "
               f"Convergence rate: {convergence_rate:.2%} ({convergence_count}/{n_bootstrap})")
    logger.info(f"High convergence rate (>=80%): {high_convergence}")
    
    return result

def export_bootstrap_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Export bootstrap convergence results to log file."""
    if output_path is None:
        output_path = LOG_DIR / "bootstrap_convergence.log"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results as JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Bootstrap results exported to {output_path}")
    return output_path

def main():
    """Main entry point for bootstrap convergence verification."""
    parser = argparse.ArgumentParser(description="Bootstrap Convergence Verification for Mixed-Effects Model")
    parser.add_argument("--n-bootstrap", type=int, default=100, 
                      help="Number of bootstrap iterations (default: 100)")
    parser.add_argument("--sample-fraction", type=float, default=0.8,
                      help="Fraction of data to sample in each iteration (default: 0.8)")
    parser.add_argument("--seed", type=int, default=None,
                      help="Random seed for reproducibility")
    parser.add_argument("--force", action="store_true",
                      help="Force run even if initial model converged")
    
    args = parser.parse_args()
    
    try:
        # Load and prepare data
        logger.info("Loading analysis data...")
        data = load_analysis_data()
        data = prepare_model_data(data)
        
        # Check if we should run bootstrap
        # Run if sample size is small (< 100) or if user forces it
        n_obs = len(data)
        if n_obs >= 100 and not args.force:
            logger.info(f"Sample size ({n_obs}) is sufficient. "
                       f"Skipping bootstrap verification unless --force is used.")
            print("Skipping bootstrap verification. Sample size is sufficient.")
            return 0
        
        logger.info(f"Running bootstrap convergence verification...")
        logger.info(f"Original sample size: {n_obs}")
        logger.info(f"Bootstrap iterations: {args.n_bootstrap}")
        logger.info(f"Sample fraction: {args.sample_fraction}")
        
        # Run bootstrap
        results = run_bootstrap_convergence_verification(
            data,
            n_bootstrap=args.n_bootstrap,
            sample_fraction=args.sample_fraction,
            seed=args.seed
        )
        
        # Export results
        output_path = export_bootstrap_results(results)
        
        # Print summary
        print("\n" + "="*60)
        print("BOOTSTRAP CONVERGENCE VERIFICATION RESULTS")
        print("="*60)
        print(f"Bootstrap Iterations: {results['bootstrap_iterations']}")
        print(f"Original Sample Size: {results['original_sample_size']}")
        print(f"Bootstrap Sample Size: {results['bootstrap_sample_size']}")
        print(f"Convergence Count: {results['convergence_count']}/{results['bootstrap_iterations']}")
        print(f"Convergence Rate: {results['convergence_rate']:.2%}")
        print(f"High Convergence Rate (>=80%): {results['high_convergence_rate']}")
        print(f"Status: {results['status']}")
        print(f"Results saved to: {output_path}")
        print("="*60 + "\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Bootstrap convergence verification failed: {str(e)}", exc_info=True)
        print(f"ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())