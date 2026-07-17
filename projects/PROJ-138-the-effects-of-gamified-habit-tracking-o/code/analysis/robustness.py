import os
import gc
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm
from multiprocessing import Pool, cpu_count
from typing import Generator, Tuple, Optional, Dict, Any
from code.utils.logging import pipeline_logger
from code.utils.config import set_random_seed

logger = pipeline_logger

def bootstrap_generator(
    data: pd.DataFrame,
    formula: str,
    n_iterations: int,
    seed: int,
    random_state: np.random.RandomState
) -> Generator[Tuple[int, float, Optional[float]], None, None]:
    """
    Generator for bootstrap iterations.
    Yields (iteration_index, gamification_coefficient, interaction_coefficient).
    """
    for i in range(n_iterations):
        # Resample with replacement
        sample_idx = random_state.choice(data.index, size=len(data), replace=True)
        sample_data = data.loc[sample_idx].copy()

        # Handle potential convergence issues or singular fits by catching exceptions
        try:
            model = mixedlm(formula, sample_data, groups=sample_data["User_ID"])
            result = model.fit(reml=False, disp=0)
            
            # Extract coefficients
            gam_coef = result.params.get("Gamified", 0.0)
            inter_coef = result.params.get("Gamified:Conscientiousness", None)
            
            yield (i, gam_coef, inter_coef)
        except Exception as e:
            # Log failure for this iteration but continue
            logger.warning(f"Bootstrap iteration {i} failed: {e}")
            continue

def _run_single_bootstrap(args: Tuple[int, pd.DataFrame, str, int]) -> Tuple[int, float, Optional[float]]:
    """
    Helper function for multiprocessing.
    Unpacks arguments and runs a single bootstrap iteration.
    """
    seed, data, formula, iteration = args
    set_random_seed(seed)
    rng = np.random.RandomState(seed)
    
    # Resample
    sample_idx = rng.choice(data.index, size=len(data), replace=True)
    sample_data = data.loc[sample_idx].copy()
    
    try:
        model = mixedlm(formula, sample_data, groups=sample_data["User_ID"])
        result = model.fit(reml=False, disp=0)
        gam_coef = result.params.get("Gamified", 0.0)
        inter_coef = result.params.get("Gamified:Conscientiousness", None)
        return (iteration, gam_coef, inter_coef)
    except Exception as e:
        logger.warning(f"Bootstrap iteration {iteration} failed in worker: {e}")
        return (iteration, np.nan, None)

def bootstrap_effect_size(
    data: pd.DataFrame,
    formula: str,
    n_iterations: int = 1000,
    n_processes: Optional[int] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Calculate bootstrapped effect sizes for gamification.
    Uses multiprocessing to parallelize iterations for performance.
    
    Returns a dictionary with:
      - 'mean_effect': Mean of bootstrapped coefficients
      - 'ci_lower': 2.5th percentile
      - 'ci_upper': 97.5th percentile
      - 'std_err': Standard deviation of bootstrapped coefficients
      - 'iterations_completed': Number of successful iterations
    """
    if n_processes is None:
        n_processes = max(1, cpu_count() - 1)
    
    logger.info(f"Starting bootstrap with {n_iterations} iterations using {n_processes} processes.")
    
    set_random_seed(seed)
    base_rng = np.random.RandomState(seed)
    
    # Prepare arguments for multiprocessing
    # We distribute the random seeds and iteration IDs
    seeds = base_rng.randint(0, 2**31, size=n_iterations)
    args_list = [(seeds[i], data, formula, i) for i in range(n_iterations)]
    
    results = []
    
    if n_processes == 1:
        # Fallback to single process if requested
        for arg in args_list:
            res = _run_single_bootstrap(arg)
            if not np.isnan(res[1]):
                results.append(res)
    else:
        # Multiprocessing
        with Pool(processes=n_processes) as pool:
            results = pool.map(_run_single_bootstrap, args_list)
    
    # Filter out failures (NaNs)
    valid_results = [r for r in results if not np.isnan(r[1])]
    
    if not valid_results:
        logger.error("No valid bootstrap iterations completed. Check data or model specification.")
        return {
            'mean_effect': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'std_err': np.nan,
            'iterations_completed': 0
        }
    
    gam_coeffs = [r[1] for r in valid_results]
    
    mean_effect = np.mean(gam_coeffs)
    std_err = np.std(gam_coeffs, ddof=1)
    ci_lower = np.percentile(gam_coeffs, 2.5)
    ci_upper = np.percentile(gam_coeffs, 97.5)
    
    logger.info(f"Bootstrap completed. {len(valid_results)}/{n_iterations} iterations successful.")
    logger.info(f"Mean Effect: {mean_effect:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    return {
        'mean_effect': mean_effect,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'std_err': std_err,
        'iterations_completed': len(valid_results),
        'all_coeffs': gam_coeffs
    }

def main():
    """
    Main entry point for running the robustness analysis.
    Loads processed data, runs bootstrapping with multiprocessing,
    and saves results to data/processed/bootstrap_results.csv.
    """
    logger.info("=== Starting Robustness Analysis (Bootstrap) ===")
    
    # Paths
    processed_data_path = "data/processed/merged_data.csv"
    output_path = "data/processed/bootstrap_results.csv"
    
    if not os.path.exists(processed_data_path):
        logger.error(f"Processed data not found at {processed_data_path}. Run ingestion/merge first.")
        return
    
    # Load data
    df = pd.read_csv(processed_data_path)
    
    # Ensure required columns exist
    required_cols = ['User_ID', 'Gamified', 'Adherence', 'Conscientiousness']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns in data: {missing}")
        return
    
    # Define formula
    # Using Adherence as outcome, Gamified and Conscientiousness as fixed effects
    # Interaction term included
    formula = "Adherence ~ Gamified * Conscientiousness"
    
    # Configuration
    n_iterations = 1000  # Sufficient for stable CI
    n_processes = 4      # Adjust based on CI constraints (CPU cores)
    
    # Run bootstrap
    results = bootstrap_effect_size(
        df,
        formula=formula,
        n_iterations=n_iterations,
        n_processes=n_processes,
        seed=42
    )
    
    # Save summary
    summary_df = pd.DataFrame([{
        'metric': 'mean_effect',
        'value': results['mean_effect']
    }, {
        'metric': 'ci_lower',
        'value': results['ci_lower']
    }, {
        'metric': 'ci_upper',
        'value': results['ci_upper']
    }, {
        'metric': 'std_err',
        'value': results['std_err']
    }, {
        'metric': 'iterations_completed',
        'value': results['iterations_completed']
    }])
    
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Bootstrap results saved to {output_path}")
    
    # Optionally save individual coefficients for plotting
    if 'all_coeffs' in results:
        coeffs_df = pd.DataFrame({
            'iteration': range(len(results['all_coeffs'])),
            'gamification_coefficient': results['all_coeffs']
        })
        coeffs_df.to_csv("data/processed/bootstrap_coefficients.csv", index=False)
    
    logger.info("=== Robustness Analysis Complete ===")

if __name__ == "__main__":
    main()