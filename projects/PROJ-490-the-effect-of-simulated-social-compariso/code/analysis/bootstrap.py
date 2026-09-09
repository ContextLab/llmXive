import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Import config for seed retrieval
from data.config import get_config
from utils.logger import get_logger, log_execution_start, log_execution_end

# Configure logger
logger = get_logger(__name__)

# Constants
MAX_BOOTSTRAP_ITERATIONS = 5000
CI_WIDTH_VARIANCE_THRESHOLD = 0.01
CONFIDENCE_LEVEL = 0.95

def run_single_bootstrap_iteration(
    df: pd.DataFrame, 
    formula: str, 
    seed: int
) -> Dict[str, float]:
    """
    Run a single bootstrap iteration:
    1. Resample rows with replacement.
    2. Fit the regression model.
    3. Return coefficients.
    """
    np.random.seed(seed)
    # Resample with replacement
    resampled_df = df.sample(n=len(df), replace=True, random_state=seed)
    
    # Fit model
    try:
        model = ols(formula, data=resampled_df).fit()
        # Return coefficients as a dict
        coeffs = {name: float(estimate) for name, estimate in model.params.items()}
        return coeffs
    except Exception as e:
        logger.warning(f"Bootstrap iteration failed: {e}")
        return None

def calculate_confidence_intervals(
    bootstrap_results: List[Dict[str, float]], 
    param_name: str,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate percentile-based confidence intervals for a specific parameter.
    """
    if not bootstrap_results:
        return (np.nan, np.nan)
    
    values = [r[param_name] for r in bootstrap_results if r and param_name in r]
    if not values:
        return (np.nan, np.nan)
    
    alpha = 1 - confidence_level
    lower = np.percentile(values, 100 * (alpha / 2))
    upper = np.percentile(values, 100 * (1 - alpha / 2))
    return (lower, upper)

def calculate_ci_width_variance(
    bootstrap_results: List[Dict[str, float]], 
    param_name: str,
    confidence_level: float = 0.95
) -> float:
    """
    Calculate the variance of the confidence interval width for a parameter.
    This is done by splitting the results into chunks (e.g., 10 chunks) and
    calculating CI width for each chunk, then taking the variance of those widths.
    """
    if len(bootstrap_results) < 20:
        return float('inf')
    
    # Split into 10 chunks for variance estimation
    n_chunks = 10
    chunk_size = len(bootstrap_results) // n_chunks
    widths = []
    
    for i in range(n_chunks):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < n_chunks - 1 else len(bootstrap_results)
        chunk = bootstrap_results[start_idx:end_idx]
        
        lower, upper = calculate_confidence_intervals(chunk, param_name, confidence_level)
        if np.isnan(lower) or np.isnan(upper):
            continue
        widths.append(upper - lower)
    
    if len(widths) < 2:
        return float('inf')
    
    return float(np.var(widths))

def run_bootstrap_stability(
    df: pd.DataFrame,
    formula: str,
    target_param: str = 'avatar_condition',
    max_iterations: int = MAX_BOOTSTRAP_ITERATIONS,
    variance_threshold: float = CI_WIDTH_VARIANCE_THRESHOLD
) -> Dict[str, Any]:
    """
    Run bootstrap analysis until stability criterion is met or max iterations reached.
    Logs the exact number of iterations and the final variance.
    """
    config = get_config()
    base_seed = config.get('bootstrap_seed', 42)
    
    logger.info(f"Starting bootstrap stability analysis for parameter: {target_param}")
    logger.info(f"Stability threshold: {variance_threshold}, Max iterations: {max_iterations}")
    
    bootstrap_results = []
    current_variance = float('inf')
    iterations_performed = 0
    stability_achieved = False
    
    for i in range(1, max_iterations + 1):
        # Deterministic seed for each iteration
        iter_seed = base_seed + i
        result = run_single_bootstrap_iteration(df, formula, iter_seed)
        
        if result:
            bootstrap_results.append(result)
        
        iterations_performed = i
        
        # Check stability every 50 iterations (or at end)
        if i % 50 == 0 or i == max_iterations:
            if len(bootstrap_results) >= 20:
                current_variance = calculate_ci_width_variance(
                    bootstrap_results, target_param
                )
                logger.debug(f"Iteration {i}: CI width variance = {current_variance:.6f}")
                
                if current_variance < variance_threshold:
                    stability_achieved = True
                    logger.info(f"Stability achieved at iteration {i} with variance {current_variance:.6f}")
                    break
    
    # Log final status
    if not stability_achieved:
        logger.warning(
            f"Bootstrap stability criterion NOT met after {iterations_performed} iterations. "
            f"Final variance: {current_variance:.6f}. "
            f"Pipeline will proceed but record this in final report."
        )
    else:
        logger.info(f"Bootstrap completed successfully in {iterations_performed} iterations.")
    
    return {
        'iterations_performed': iterations_performed,
        'final_variance': current_variance,
        'stability_achieved': stability_achieved,
        'results': bootstrap_results
    }

def run_bootstrap_analysis(
    df: pd.DataFrame,
    formula: str,
    target_param: str = 'avatar_condition',
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main entry point for bootstrap analysis.
    Returns a dictionary containing stability metrics and results.
    """
    log_execution_start(logger, "run_bootstrap_analysis")
    
    if output_dir is None:
        output_dir = Path("data/processed")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run stability analysis
    stability_data = run_bootstrap_stability(df, formula, target_param)
    
    # Calculate final CIs using all collected results
    final_lower, final_upper = calculate_confidence_intervals(
        stability_data['results'], target_param
    )
    
    result_dict = {
        'target_parameter': target_param,
        'iterations_performed': stability_data['iterations_performed'],
        'final_ci_variance': stability_data['final_variance'],
        'stability_failed': not stability_data['stability_achieved'],
        'confidence_interval': {
            'lower': final_lower,
            'upper': final_upper,
            'level': CONFIDENCE_LEVEL
        },
        'raw_results_count': len(stability_data['results'])
    }
    
    # Save intermediate bootstrap results for debugging (optional)
    results_path = output_dir / "bootstrap_raw_results.csv"
    if stability_data['results']:
        pd.DataFrame(stability_data['results']).to_csv(results_path, index=False)
        logger.info(f"Saved raw bootstrap results to {results_path}")
    
    log_execution_end(logger, "run_bootstrap_analysis", result_dict)
    return result_dict

def main():
    """
    Standalone execution for testing/bootstrap verification.
    Expects data to be available at data/processed/imputed_data.csv
    """
    logger.info("Running bootstrap analysis standalone...")
    
    # Load data
    data_path = Path("data/processed/imputed_data.csv")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return
    
    df = pd.read_csv(data_path)
    
    # Define formula based on project spec (ANCOVA)
    # Outcome: post_self_esteem, Covariate: pre_self_esteem, Predictors: avatar_condition, comparison_tendency
    formula = "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + avatar_condition:comparison_tendency"
    
    # Run analysis
    results = run_bootstrap_analysis(df, formula)
    
    # Print summary
    print(f"\n--- Bootstrap Analysis Summary ---")
    print(f"Iterations: {results['iterations_performed']}")
    print(f"Stability Failed: {results['stability_failed']}")
    print(f"Final Variance: {results['final_ci_variance']}")
    print(f"95% CI: [{results['confidence_interval']['lower']:.4f}, {results['confidence_interval']['upper']:.4f}]")
    
    return results

if __name__ == "__main__":
    main()
