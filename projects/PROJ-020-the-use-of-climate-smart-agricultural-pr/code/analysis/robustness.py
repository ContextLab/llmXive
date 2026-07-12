"""
Robustness analysis module for the CSA Food Security study.
Implements leave-one-region-out cross-validation and bootstrap resampling.
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from tqdm import tqdm
import statsmodels.api as sm
import statsmodels.formula.api as smf
from concurrent.futures import ProcessPoolExecutor, as_completed
import pickle
import json
import os
import sys
import time

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_BOOTSTRAP_ITERATIONS = 1000
DEFAULT_SEED = 42
DEFAULT_FRACTION = 0.8  # Bootstrap sample size as fraction of original
DEFAULT_N_JOBS = -1  # Use all available CPUs

def _fit_model_on_sample(
    data: pd.DataFrame,
    formula: str,
    random_effect: str,
    weights_col: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Helper function to fit a mixed-effects model on a specific sample.
    Designed to be pickled for multiprocessing.
    """
    if seed is not None:
        np.random.seed(seed + hash(str(data.shape)) % 1000)

    try:
        # Sample data if needed (handled by caller, but safety check)
        sample_df = data.copy()
        
        # Prepare weights if provided
        if weights_col and weights_col in sample_df.columns:
            sample_df = sample_df.dropna(subset=[weights_col])
            weights = sample_df[weights_col]
            model = smf.mixedlm(formula, sample_df, 
                              groups=sample_df[random_effect], 
                              weights=weights)
        else:
            model = smf.mixedlm(formula, sample_df, 
                              groups=sample_df[random_effect])
        
        # Fit with some robustness against convergence issues
        result = model.fit(reml=False, maxiter=100)
        
        return {
            "success": True,
            "coefficients": result.params.to_dict(),
            "std_errors": result.bse.to_dict(),
            "pvalues": result.pvalues.to_dict(),
            "log_likelihood": result.llf,
            "aic": result.aic,
            "bic": result.bic,
            "random_effects_variance": result.random_effects_variance
        }
    except Exception as e:
        logger.warning(f"Model fitting failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def run_bootstrap_resampling(
    data: pd.DataFrame,
    formula: str,
    random_effect: str,
    weights_col: Optional[str] = None,
    n_iterations: int = DEFAULT_BOOTSTRAP_ITERATIONS,
    fraction: float = DEFAULT_FRACTION,
    seed: int = DEFAULT_SEED,
    output_dir: Optional[Path] = None,
    n_jobs: int = DEFAULT_N_JOBS
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to validate model stability and report variance estimates.
    
    Args:
        data: Processed dataset with all variables
        formula: Statsmodels formula string (e.g., "food_security ~ csa_index + controls")
        random_effect: Name of the grouping variable for random effects (e.g., "region")
        weights_col: Optional column name for sampling weights
        n_iterations: Number of bootstrap iterations
        fraction: Fraction of data to sample in each iteration
        seed: Random seed for reproducibility
        output_dir: Directory to save results
        n_jobs: Number of parallel processes (-1 for all CPUs)
        
    Returns:
        Dictionary containing:
        - coefficients: Mean coefficients across bootstrap samples
        - std_errors: Standard deviation of coefficients (bootstrap SE)
        - confidence_intervals: 95% CI for each coefficient
        - convergence_rate: Percentage of successful model fits
        - original_model_stats: Stats from the full dataset model
    """
    logger.info(f"Starting bootstrap resampling with {n_iterations} iterations...")
    logger.info(f"Data shape: {data.shape}, Sampling fraction: {fraction}")
    
    # Ensure output directory exists
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # First, fit the model on the full dataset
    logger.info("Fitting model on full dataset...")
    try:
        full_sample = data.copy()
        if weights_col and weights_col in full_sample.columns:
            full_sample = full_sample.dropna(subset=[weights_col])
            weights = full_sample[weights_col]
            full_model = smf.mixedlm(formula, full_sample, 
                                  groups=full_sample[random_effect], 
                                  weights=weights)
        else:
            full_model = smf.mixedlm(formula, full_sample, 
                                  groups=full_sample[random_effect])
        
        full_result = full_model.fit(reml=False, maxiter=100)
        original_stats = {
            "coefficients": full_result.params.to_dict(),
            "std_errors": full_result.bse.to_dict(),
            "pvalues": full_result.pvalues.to_dict(),
            "log_likelihood": float(full_result.llf),
            "aic": float(full_result.aic),
            "bic": float(full_result.bic)
        }
    except Exception as e:
        logger.error(f"Failed to fit full dataset model: {str(e)}")
        original_stats = {}
    
    # Prepare for bootstrap
    n_samples = int(len(data) * fraction)
    results = []
    successful_fits = 0
    
    # Use multiprocessing for speed
    if n_jobs == 1:
        # Sequential execution
        logger.info("Running bootstrap sequentially...")
        for i in tqdm(range(n_iterations), desc="Bootstrap iterations"):
            # Sample with replacement
            sample_idx = np.random.choice(len(data), size=n_samples, replace=True)
            sample_data = data.iloc[sample_idx].reset_index(drop=True)
            
            # Set seed for this iteration
            iter_seed = seed + i
            np.random.seed(iter_seed)
            
            result = _fit_model_on_sample(
                sample_data, formula, random_effect, 
                weights_col=weights_col, seed=iter_seed
            )
            
            if result["success"]:
                results.append(result["coefficients"])
                successful_fits += 1
    else:
        # Parallel execution
        logger.info(f"Running bootstrap with {n_jobs} processes...")
        tasks = []
        for i in range(n_iterations):
            sample_idx = np.random.choice(len(data), size=n_samples, replace=True)
            sample_data = data.iloc[sample_idx].reset_index(drop=True)
            iter_seed = seed + i
            
            tasks.append((sample_data, formula, random_effect, weights_col, iter_seed))
        
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            futures = [executor.submit(_fit_model_on_sample, *task) for task in tasks]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Bootstrap iterations"):
                result = future.result()
                if result["success"]:
                    results.append(result["coefficients"])
                    successful_fits += 1
    
    # Calculate statistics
    convergence_rate = successful_fits / n_iterations if n_iterations > 0 else 0
    logger.info(f"Bootstrap completed. Convergence rate: {convergence_rate:.2%}")
    
    if not results:
        logger.error("No successful bootstrap fits. Returning empty results.")
        return {
            "coefficients": {},
            "std_errors": {},
            "confidence_intervals": {},
            "convergence_rate": 0.0,
            "original_model_stats": original_stats,
            "iterations": n_iterations,
            "successes": 0
        }
    
    # Convert to DataFrame for easy calculation
    results_df = pd.DataFrame(results)
    
    # Calculate mean coefficients and bootstrap standard errors
    mean_coeffs = results_df.mean()
    bootstrap_se = results_df.std()
    
    # Calculate 95% confidence intervals using percentile method
    confidence_intervals = {}
    for col in results_df.columns:
        lower = results_df[col].quantile(0.025)
        upper = results_df[col].quantile(0.975)
        confidence_intervals[col] = {"lower": lower, "upper": upper}
    
    # Prepare final results
    bootstrap_results = {
        "coefficients": mean_coeffs.to_dict(),
        "std_errors": bootstrap_se.to_dict(),
        "confidence_intervals": confidence_intervals,
        "convergence_rate": convergence_rate,
        "original_model_stats": original_stats,
        "iterations": n_iterations,
        "successes": successful_fits,
        "fraction": fraction,
        "seed": seed
    }
    
    # Save results if output_dir provided
    if output_dir:
        results_file = output_dir / "bootstrap_results.json"
        with open(results_file, 'w') as f:
            json.dump(bootstrap_results, f, indent=2, default=str)
        
        # Save detailed results for each iteration
        detailed_file = output_dir / "bootstrap_detailed.csv"
        results_df.to_csv(detailed_file)
        
        logger.info(f"Bootstrap results saved to {output_dir}")
    
    return bootstrap_results

def run_leave_one_region_out(
    data: pd.DataFrame,
    formula: str,
    random_effect: str,
    weights_col: Optional[str] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Perform leave-one-region-out cross-validation.
    
    Args:
        data: Processed dataset
        formula: Statsmodels formula
        random_effect: Grouping variable (region)
        weights_col: Optional weights column
        output_dir: Directory to save results
        
    Returns:
        Dictionary with results for each left-out region
    """
    logger.info("Starting leave-one-region-out cross-validation...")
    
    # Get unique regions
    regions = data[random_effect].unique()
    logger.info(f"Found {len(regions)} regions to iterate over")
    
    results = {}
    
    for region in tqdm(regions, desc="Leave-one-region-out"):
        # Create training set (exclude current region)
        train_data = data[data[random_effect] != region]
        
        if len(train_data) == 0:
            logger.warning(f"Skipping region {region}: no data left after exclusion")
            continue
        
        try:
            # Fit model
            if weights_col and weights_col in train_data.columns:
                train_data = train_data.dropna(subset=[weights_col])
                weights = train_data[weights_col]
                model = smf.mixedlm(formula, train_data, 
                                  groups=train_data[random_effect], 
                                  weights=weights)
            else:
                model = smf.mixedlm(formula, train_data, 
                                  groups=train_data[random_effect])
            
            result = model.fit(reml=False, maxiter=100)
            
            results[region] = {
                "success": True,
                "coefficients": result.params.to_dict(),
                "log_likelihood": float(result.llf),
                "aic": float(result.aic),
                "sample_size": len(train_data)
            }
        except Exception as e:
            logger.warning(f"Failed for region {region}: {str(e)}")
            results[region] = {
                "success": False,
                "error": str(e)
            }
    
    # Calculate stability metrics
    if results:
        successful_regions = {k: v for k, v in results.items() if v.get("success")}
        if successful_regions:
            coeff_values = pd.DataFrame({k: v["coefficients"] for k, v in successful_regions.items()})
            stability_metrics = {
                "coefficient_std": coeff_values.std().to_dict(),
                "coefficient_mean": coeff_values.mean().to_dict(),
                "regions_success_rate": len(successful_regions) / len(regions)
            }
        else:
            stability_metrics = {}
    else:
        stability_metrics = {}
    
    final_results = {
        "region_results": results,
        "stability_metrics": stability_metrics,
        "total_regions": len(regions),
        "successful_iterations": len([r for r in results.values() if r.get("success")])
    }
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "leave_one_region_out.json", 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
    
    return final_results

def run_robustness_pipeline(
    data: pd.DataFrame,
    formula: str,
    random_effect: str,
    weights_col: Optional[str] = None,
    bootstrap_iterations: int = 1000,
    output_dir: Optional[Path] = None,
    n_jobs: int = -1
) -> Dict[str, Any]:
    """
    Run the complete robustness analysis pipeline.
    
    Args:
        data: Processed dataset
        formula: Statsmodels formula
        random_effect: Grouping variable
        weights_col: Optional weights column
        bootstrap_iterations: Number of bootstrap iterations
        output_dir: Directory to save results
        n_jobs: Number of parallel processes
        
    Returns:
        Dictionary with all robustness results
    """
    logger.info("Starting robustness pipeline...")
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run bootstrap resampling
    bootstrap_results = run_bootstrap_resampling(
        data=data,
        formula=formula,
        random_effect=random_effect,
        weights_col=weights_col,
        n_iterations=bootstrap_iterations,
        output_dir=output_dir,
        n_jobs=n_jobs
    )
    
    # Run leave-one-region-out
    lor_results = run_leave_one_region_out(
        data=data,
        formula=formula,
        random_effect=random_effect,
        weights_col=weights_col,
        output_dir=output_dir
    )
    
    # Compile final report
    pipeline_results = {
        "bootstrap": bootstrap_results,
        "leave_one_region_out": lor_results,
        "summary": {
            "bootstrap_convergence_rate": bootstrap_results.get("convergence_rate", 0),
            "lor_success_rate": lor_results.get("successful_iterations", 0) / max(lor_results.get("total_regions", 1), 1),
            "bootstrap_iterations": bootstrap_iterations
        }
    }
    
    if output_dir:
        with open(output_dir / "robustness_pipeline_results.json", 'w') as f:
            json.dump(pipeline_results, f, indent=2, default=str)
        logger.info(f"Robustness pipeline results saved to {output_dir}")
    
    return pipeline_results

def main():
    """Main entry point for robustness analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run robustness analysis")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data parquet file")
    parser.add_argument("--formula", type=str, default="food_security ~ csa_index + household_size + education + age",
                      help="Statsmodels formula")
    parser.add_argument("--random-effect", type=str, default="region", help="Random effect grouping variable")
    parser.add_argument("--weights", type=str, default=None, help="Column name for sampling weights")
    parser.add_argument("--bootstrap-iterations", type=int, default=1000, help="Number of bootstrap iterations")
    parser.add_argument("--output-dir", type=str, default="data/processed/robustness", help="Output directory")
    parser.add_argument("--n-jobs", type=int, default=-1, help="Number of parallel processes")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load data
    logger.info(f"Loading data from {args.data}")
    data = pd.read_parquet(args.data)
    logger.info(f"Loaded {len(data)} rows")
    
    # Run pipeline
    results = run_robustness_pipeline(
        data=data,
        formula=args.formula,
        random_effect=args.random_effect,
        weights_col=args.weights,
        bootstrap_iterations=args.bootstrap_iterations,
        output_dir=Path(args.output_dir),
        n_jobs=args.n_jobs
    )
    
    logger.info("Robustness pipeline completed successfully")
    print(json.dumps(results["summary"], indent=2))

if __name__ == "__main__":
    main()