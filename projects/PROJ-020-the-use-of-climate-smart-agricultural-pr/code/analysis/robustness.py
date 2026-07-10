"""
Robustness checks for the CSA-Food Security analysis.

Implements:
- Leave-One-Region-Out (LORO) cross-validation
- Bootstrap resampling for model stability
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from tqdm import tqdm
import statsmodels.formula.api as smf

from utils.config import get_processed_data_dir, get_state_dir
from analysis.model import run_mixed_effects_model

logger = logging.getLogger(__name__)

def run_leave_one_region_out(
    data: pd.DataFrame,
    formula: str,
    region_column: str = "region",
    random_effect: str = "country",
    n_bootstraps: int = 50,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform Leave-One-Region-Out cross-validation.
    
    For each unique region in the data:
    1. Exclude that region from the training set.
    2. Fit the mixed-effects model on the remaining data.
    3. Record the coefficients and standard errors.
    
    Returns a dictionary containing:
    - 'full_model': Results from the model trained on all data.
    - 'loro_results': List of results for each excluded region.
    - 'stability_metrics': Variance of coefficients across folds.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if region_column not in data.columns:
        raise ValueError(f"Region column '{region_column}' not found in data. "
                         f"Available columns: {list(data.columns)}")
    
    regions = data[region_column].unique()
    logger.info(f"Starting Leave-One-Region-Out CV. Total regions: {len(regions)}")
    
    # 1. Fit full model
    logger.info("Fitting full model on all data...")
    try:
        full_results = run_mixed_effects_model(
            data, formula, random_effect=random_effect
        )
        full_coeffs = full_results.params
    except Exception as e:
        logger.error(f"Failed to fit full model: {e}")
        return {"error": str(e), "status": "failed"}
    
    loro_results = []
    all_coeffs = [full_coeffs]
    
    # 2. Iterate through regions
    for i, region in enumerate(tqdm(regions, desc="LORO Iterations")):
        # Filter out current region
        train_data = data[data[region_column] != region].copy()
        
        if len(train_data) < 100:
            logger.warning(f"Region {region} excluded. Remaining data too small ({len(train_data)}). Skipping.")
            continue
        
        try:
            # Fit model
            model_res = run_mixed_effects_model(
                train_data, formula, random_effect=random_effect
            )
            
            # Extract fixed effects coefficients
            fixed_coeffs = model_res.params
            
            loro_entry = {
                "excluded_region": region,
                "n_observations": len(train_data),
                "coefficients": fixed_coeffs.to_dict(),
                "p_values": model_res.pvalues.to_dict()
            }
            loro_results.append(loro_entry)
            all_coeffs.append(fixed_coeffs)
            
        except Exception as e:
            logger.warning(f"Model failed for region {region} (excluded): {e}")
            loro_results.append({
                "excluded_region": region,
                "error": str(e)
            })
    
    # 3. Calculate stability metrics
    if len(all_coeffs) > 1:
        coeffs_df = pd.DataFrame(all_coeffs).T
        stability = {
            "mean_coefficient": coeffs_df.mean().to_dict(),
            "std_coefficient": coeffs_df.std().to_dict(),
            "variance_coefficient": coeffs_df.var().to_dict(),
            "max_deviation": (coeffs_df - full_coeffs).abs().max().to_dict()
        }
    else:
        stability = {}
    
    return {
        "full_model": {
            "params": full_coeffs.to_dict(),
            "pvalues": full_results.pvalues.to_dict()
        },
        "loro_results": loro_results,
        "stability_metrics": stability,
        "n_regions": len(regions),
        "n_successful_folds": len(loro_results)
    }

def run_bootstrap_resampling(
    data: pd.DataFrame,
    formula: str,
    random_effect: str = "country",
    n_iterations: int = 200,
    sample_fraction: float = 0.8,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to validate model stability.
    
    Repeatedly samples a fraction of the data with replacement,
    fits the model, and aggregates coefficient distributions.
    
    Returns:
    - 'bootstrap_distributions': Dict of coefficient -> list of values.
    - 'summary': Mean, std, and 95% CI for each coefficient.
    """
    if seed is not None:
        np.random.seed(seed)
    
    logger.info(f"Starting Bootstrap Resampling. Iterations: {n_iterations}, Sample fraction: {sample_fraction}")
    
    bootstrap_coeffs = {}
    
    # Pre-extract coefficient names from a single run
    try:
        temp_model = run_mixed_effects_model(data, formula, random_effect=random_effect)
        coef_names = temp_model.params.index.tolist()
        for name in coef_names:
            bootstrap_coeffs[name] = []
    except Exception as e:
        logger.error(f"Could not determine coefficient names for bootstrap: {e}")
        return {"error": str(e), "status": "failed"}
    
    n_samples = len(data)
    sample_size = int(n_samples * sample_fraction)
    
    for i in tqdm(range(n_iterations), desc="Bootstrap Iterations"):
        # Resample rows with replacement
        # We sample by index to handle potential duplicate indices
        resampled_indices = np.random.choice(data.index, size=sample_size, replace=True)
        resampled_data = data.loc[resampled_indices]
        
        try:
            model_res = run_mixed_effects_model(
                resampled_data, formula, random_effect=random_effect
            )
            
            # Store coefficients
            for name in coef_names:
                if name in model_res.params.index:
                    bootstrap_coeffs[name].append(model_res.params[name])
                else:
                    bootstrap_coeffs[name].append(np.nan)
                    
        except Exception as e:
            # Log but continue; some bootstrap samples might fail convergence
            logger.debug(f"Bootstrap iteration {i} failed: {e}")
            continue
    
    # Calculate statistics
    summary = {}
    for name, values in bootstrap_coeffs.items():
        valid_values = [v for v in values if not np.isnan(v)]
        if len(valid_values) > 0:
            arr = np.array(valid_values)
            summary[name] = {
                "mean": float(np.mean(arr)),
                "std": float(np.std(arr)),
                "ci_95_lower": float(np.percentile(arr, 2.5)),
                "ci_95_upper": float(np.percentile(arr, 97.5)),
                "n_success": len(valid_values)
            }
        else:
            summary[name] = {
                "mean": np.nan,
                "std": np.nan,
                "ci_95_lower": np.nan,
                "ci_95_upper": np.nan,
                "n_success": 0
            }
    
    return {
        "n_iterations_requested": n_iterations,
        "n_iterations_successful": sum(1 for v in summary.values() if v["n_success"] > 0),
        "summary": summary,
        "distributions": {k: v for k, v in bootstrap_coeffs.items()} # Keep raw for plotting if needed
    }

def run_robustness_pipeline(
    data_path: Optional[Path] = None,
    formula: Optional[str] = None,
    region_column: str = "region",
    random_effect: str = "country",
    n_loro_folds: int = 5, # Number of regions to test if too many, or None for all
    n_bootstrap: int = 100,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Orchestrates the full robustness check pipeline.
    
    Loads data, runs LORO and Bootstrap, and saves results to JSON.
    """
    if output_dir is None:
        output_dir = get_state_dir() / "robustness"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data if path provided
    if data_path is None:
        data_path = get_processed_data_dir() / "merged_sample.parquet"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    logger.info(f"Loading data from {data_path}")
    data = pd.read_parquet(data_path)
    
    # Default formula if not provided (matches typical US2 model structure)
    if formula is None:
        # Assuming CSA index is the main predictor, food security as outcome
        # Includes controls and interactions as per US2
        formula = "food_security_index ~ csa_index + digital_access + finance_access + " \
                  "csa_index:digital_access + csa_index:finance_access + " \
                  "age + education_years + household_size + plot_size"
    
    logger.info(f"Using formula: {formula}")
    
    # 1. Leave-One-Region-Out
    logger.info("Running Leave-One-Region-Out...")
    loro_results = run_leave_one_region_out(
        data, 
        formula, 
        region_column=region_column, 
        random_effect=random_effect
    )
    
    # 2. Bootstrap
    logger.info("Running Bootstrap Resampling...")
    bootstrap_results = run_bootstrap_resampling(
        data, 
        formula, 
        random_effect=random_effect,
        n_iterations=n_bootstrap
    )
    
    # Save results
    output_file = output_dir / "robustness_results.json"
    import json
    with open(output_file, 'w') as f:
        json.dump({
            "loro": loro_results,
            "bootstrap": bootstrap_results
        }, f, indent=2, default=str)
    
    logger.info(f"Robustness results saved to {output_file}")
    return output_file

def main():
    """Entry point for robustness checks."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        output_path = run_robustness_pipeline()
        print(f"Robustness pipeline completed. Results: {output_path}")
    except Exception as e:
        logger.error(f"Robustness pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
