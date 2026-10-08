import json
import logging
import sys
import zipfile
from io import StringIO
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.power import Power
from scipy import stats

from config import get_processed_data_dir, get_project_root
from logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def load_synthetic_datasets(zip_path: Path) -> list:
    """
    Loads synthetic datasets from the provided zip file.
    Returns a list of DataFrames.
    """
    datasets = []
    if not zip_path.exists():
        raise FileNotFoundError(f"Synthetic zip file not found: {zip_path}")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for file_name in zf.namelist():
            if file_name.endswith('.csv'):
                with zf.open(file_name) as f:
                    df = pd.read_csv(StringIO(f.read().decode('utf-8')))
                    datasets.append(df)
    
    if not datasets:
        raise ValueError("No CSV files found in the synthetic zip archive.")
    
    logger.info(f"Loaded {len(datasets)} synthetic datasets.")
    return datasets

def run_lmm_simulation(data: pd.DataFrame) -> dict:
    """
    Runs a simplified LMM simulation (using OLS with fixed effects as proxy 
    for power analysis context or statsmodels MixedLM if available).
    For power analysis, we often simulate the F-statistic or t-statistic distribution.
    
    Here we fit a model: rating ~ relationship * cue_intensity
    and extract the F-statistic for the interaction term to estimate power.
    """
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import ols
        
        # Fit OLS as a proxy for fixed effects in the power simulation context
        # In a full LMM, we'd use MixedLM, but for power estimation on fixed effects
        # with simulated data where random effects are already integrated or controlled,
        # OLS is often used for the primary effect estimation in simulation loops.
        model = ols('rating ~ relationship * cue_intensity', data=data).fit()
        
        # Get the F-statistic for the interaction term
        # The interaction term involves multiple coefficients if categorical,
        # but for power analysis simulation, we look at the overall model significance
        # or the specific interaction F-test.
        
        # Let's assume 'relationship' and 'cue_intensity' are categorical or continuous.
        # If we treat them as factors, we need an ANOVA table.
        anova_table = sm.stats.anova_lm(model, typ=2)
        
        interaction_row = anova_table.loc['relationship:cue_intensity']
        f_stat = interaction_row['F']
        p_value = interaction_row['PR(>F)']
        
        return {
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "r_squared": float(model.rsquared),
            "n_obs": len(data)
        }
    except ImportError:
        logger.error("statsmodels not found. Please install it.")
        raise

def estimate_power(results: list, alpha: float = 0.05) -> float:
    """
    Estimates power based on the proportion of simulations where p < alpha.
    """
    significant_count = sum(1 for r in results if r['p_value'] < alpha)
    return significant_count / len(results)

def calculate_target_n(estimated_power: float, target_power: float = 0.80, current_n: int = 60) -> int:
    """
    Roughly estimates the required N to reach target_power.
    Uses a linear interpolation approximation for simplicity in this script.
    Power roughly scales with sqrt(N).
    Target_N = Current_N * (Target_Power / Current_Power)^2
    """
    if estimated_power <= 0:
        return current_n * 10  # Default fallback
    
    # Avoid division by zero or extremely small numbers
    safe_power = max(estimated_power, 0.01)
    
    ratio = target_power / safe_power
    target_n = int(current_n * (ratio ** 2))
    
    return max(target_n, current_n)

def main():
    """
    Main entry point for the power analysis simulation.
    1. Loads synthetic datasets from data/processed/synthetic_power_datasets.zip
    2. Runs LMM simulation on each.
    3. Aggregates results to estimate power.
    4. Calculates target N.
    5. Saves results to data/processed/power_analysis_results.json.
    """
    setup_logging()
    
    project_root = get_project_root()
    zip_path = project_root / "data" / "processed" / "synthetic_power_datasets.zip"
    output_path = project_root / "data" / "processed" / "power_analysis_results.json"
    
    logger.info(f"Starting power analysis simulation. Input: {zip_path}")
    
    try:
        datasets = load_synthetic_datasets(zip_path)
    except Exception as e:
        logger.critical(f"Failed to load synthetic datasets: {e}")
        raise

    simulation_results = []
    
    for i, df in enumerate(datasets):
        logger.info(f"Running simulation on dataset {i+1}/{len(datasets)} (N={len(df)})")
        try:
            result = run_lmm_simulation(df)
            simulation_results.append(result)
        except Exception as e:
            logger.warning(f"Simulation failed for dataset {i}: {e}")
            # If a dataset fails, we might want to skip or count as non-significant.
            # For power analysis, a crash usually means the data was malformed.
            # We'll log it and continue, treating it as a non-rejection (p=1.0) 
            # or simply skip it if the count is too low.
            simulation_results.append({"f_statistic": 0.0, "p_value": 1.0, "r_squared": 0.0, "n_obs": len(df)})
    
    if not simulation_results:
        raise RuntimeError("No simulation results generated.")
    
    estimated_power = estimate_power(simulation_results)
    logger.info(f"Estimated Power: {estimated_power:.4f}")
    
    # Calculate target N based on the average N of the simulated datasets
    avg_n = int(np.mean([r['n_obs'] for r in simulation_results]))
    target_n = calculate_target_n(estimated_power, target_power=0.80, current_n=avg_n)
    logger.info(f"Target N for 80% power: {target_n}")
    
    output_data = {
        "estimated_power": estimated_power,
        "target_N": target_n,
        "method": "Monte Carlo simulation using synthetic datasets",
        "simulations_run": len(simulation_results),
        "average_n_per_simulation": avg_n,
        "alpha_threshold": 0.05,
        "details": simulation_results
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Power analysis results saved to {output_path}")
    print(f"Power Analysis Complete: Power={estimated_power:.4f}, Target N={target_n}")

if __name__ == "__main__":
    main()