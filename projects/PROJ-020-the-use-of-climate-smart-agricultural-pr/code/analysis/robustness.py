"""
Robustness Analysis Module
Implements leave-one-country-out cross-validation and bootstrap resampling.
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from tqdm import tqdm
import json
import statsmodels.formula.api as smf

from utils.config import get_processed_data_dir, get_state_dir

logger = logging.getLogger(__name__)

def load_model_results(results_path: Optional[str] = None) -> pd.DataFrame:
    """Load model results from JSON/Parquet if available, otherwise return None."""
    if results_path and Path(results_path).exists():
        return pd.read_json(results_path)
    return None

def run_bootstrap_resampling(
    data: pd.DataFrame,
    formula: str,
    n_iterations: int = 100,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to validate model stability.
    
    Args:
        data: The analysis dataset.
        formula: The model formula.
        n_iterations: Number of bootstrap iterations.
        random_state: Random seed.
        
    Returns:
        Dictionary containing coefficient estimates and confidence intervals.
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    n = len(data)
    coefficients = {key: [] for key in ["csa_index", "intercept"]} # Simplified for robustness check
    
    logger.info(f"Running {n_iterations} bootstrap iterations...")
    
    for i in tqdm(range(n_iterations)):
        # Resample with replacement
        sample_idx = np.random.choice(n, size=n, replace=True)
        sample_data = data.iloc[sample_idx]
        
        try:
            # Fit model on bootstrap sample
            # Note: Using OLS for speed in bootstrap, matching main model strategy
            model = smf.ols(formula=formula, data=sample_data).fit()
            
            # Extract coefficients (handling potential missing predictors in subsample)
            if "csa_index" in model.params.index:
                coefficients["csa_index"].append(model.params["csa_index"])
            if "intercept" in model.params.index:
                coefficients["intercept"].append(model.params["intercept"])
                
        except Exception as e:
            logger.warning(f"Bootstrap iteration {i} failed: {e}")
            continue
    
    # Calculate statistics
    results = {}
    for key, values in coefficients.items():
        if values:
            results[key] = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "ci_lower": float(np.percentile(values, 2.5)),
                "ci_upper": float(np.percentile(values, 97.5)),
                "n_successful": len(values)
            }
        else:
            results[key] = {"error": "No successful iterations"}
            
    return results

def run_leave_one_region_out(
    data: pd.DataFrame,
    formula: str,
    region_col: str = "country"
) -> Dict[str, Any]:
    """
    Perform leave-one-country-out cross-validation.
    
    Args:
        data: The analysis dataset.
        formula: The model formula.
        region_col: Column name for the region/country.
        
    Returns:
        Dictionary containing coefficient stability metrics.
    """
    unique_regions = data[region_col].unique()
    if len(unique_regions) < 2:
        logger.warning("Not enough regions to perform leave-one-out.")
        return {}
        
    results = []
    
    logger.info(f"Running leave-one-{region_col}-out cross-validation...")
    
    for region in unique_regions:
        # Exclude one region
        train_data = data[data[region_col] != region]
        
        try:
            model = smf.ols(formula=formula, data=train_data).fit()
            
            # Extract key coefficient
            csa_coef = model.params.get("csa_index", None)
            
            results.append({
                "excluded_region": region,
                "csa_coefficient": csa_coef,
                "n_obs": len(train_data),
                "r_squared": model.rsquared
            })
            
        except Exception as e:
            logger.warning(f"LOO iteration for region {region} failed: {e}")
            continue
            
    # Calculate stability metrics
    if results:
        coeffs = [r["csa_coefficient"] for r in results if r["csa_coefficient"] is not None]
        stability = {
            "n_folds": len(results),
            "mean_coefficient": float(np.mean(coeffs)) if coeffs else None,
            "std_coefficient": float(np.std(coeffs)) if coeffs else None,
            "min_coefficient": float(np.min(coeffs)) if coeffs else None,
            "max_coefficient": float(np.max(coeffs)) if coeffs else None,
            "details": results
        }
        return stability
    return {}

def run_robustness_pipeline(
    data: pd.DataFrame,
    formula: str,
    output_dir: Optional[Path] = None,
    bootstrap_iterations: int = 100
) -> Dict[str, Any]:
    """
    Run the full robustness pipeline: LOO and Bootstrap.
    """
    if output_dir is None:
        output_dir = get_state_dir()
        
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # 1. Leave-One-Country-Out
    try:
        loo_results = run_leave_one_region_out(data, formula)
        results["leave_one_country_out"] = loo_results
        # Save LOO results
        with open(output_dir / "loo_results.json", "w") as f:
            json.dump(loo_results, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"LOO analysis failed: {e}")
        results["leave_one_country_out"] = {"error": str(e)}
        
    # 2. Bootstrap
    try:
        boot_results = run_bootstrap_resampling(data, formula, n_iterations=bootstrap_iterations)
        results["bootstrap"] = boot_results
        # Save Bootstrap results
        with open(output_dir / "bootstrap_results.json", "w") as f:
            json.dump(boot_results, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Bootstrap analysis failed: {e}")
        results["bootstrap"] = {"error": str(e)}
        
    return results

def main():
    """
    Main entry point for robustness checks.
    Requires --data argument to be passed via CLI.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run robustness checks on model results.")
    parser.add_argument("--data", type=str, required=True, help="Path to the processed dataset (parquet).")
    parser.add_argument("--formula", type=str, default="food_security ~ csa_index + country_dummies", help="Model formula.")
    parser.add_argument("--random-effect", type=str, default=None, help="Random effect specification (not used in fixed-effects).")
    parser.add_argument("--weights", type=str, default=None, help="Sampling weights column.")
    parser.add_argument("--bootstrap-iterations", type=int, default=100, help="Number of bootstrap iterations.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for results.")
    parser.add_argument("--n-jobs", type=int, default=1, help="Number of parallel jobs (not implemented yet).")
    
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.data}")
    
    if not Path(args.data).exists():
        raise FileNotFoundError(f"Data file not found: {args.data}")
        
    data = pd.read_parquet(args.data)
    
    # Basic validation
    if "csa_index" not in data.columns:
        logger.warning("csa_index not found in data. Attempting to use 'CSA_Index' or similar.")
        # Try to find a similar column
        matching_cols = [c for c in data.columns if "csa" in c.lower()]
        if matching_cols:
            data["csa_index"] = data[matching_cols[0]]
            logger.info(f"Using column {matching_cols[0]} as csa_index.")
        else:
            raise ValueError("Could not find CSA index column in dataset.")
            
    if "country" not in data.columns:
        raise ValueError("Country column not found in dataset.")
        
    output_dir = Path(args.output_dir) if args.output_dir else get_state_dir()
    
    results = run_robustness_pipeline(
        data=data,
        formula=args.formula,
        output_dir=output_dir,
        bootstrap_iterations=args.bootstrap_iterations
    )
    
    # Save final summary
    summary_path = output_dir / "robustness_summary.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
        
    logger.info(f"Robustness analysis complete. Results saved to {summary_path}")

if __name__ == "__main__":
    main()
