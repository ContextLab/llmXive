"""
Task T091: Run Power-Analysis Simulation

Executes the power analysis simulation using the synthetic datasets generated in T090b.
Reads the synthetic zip file, runs LMM simulations, estimates power, and calculates
the required target N to achieve >= 0.80 power.

Output: data/processed/power_analysis_results.json
"""
import json
import logging
import sys
import zipfile
from io import StringIO
from pathlib import Path
import csv
import random
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.power import TTestIndPower

# Local imports matching the API surface
from config import get_processed_data_dir, get_data_dir
from logging_config import setup_logging, get_logger

# Initialize logging
logger = setup_logging()
logger = get_logger(__name__)

def load_synthetic_datasets(zip_path: Path) -> pd.DataFrame:
    """
    Loads the synthetic dataset from the zip file generated in T090b.
    Reads the CSV content from within the zip.
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Synthetic dataset zip file not found: {zip_path}")
    
    logger.info(f"Loading synthetic datasets from {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Assume the zip contains a single CSV file or we look for .csv
        csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
        if not csv_files:
            raise ValueError(f"No CSV files found in {zip_path}")
        
        # Load the first (or only) CSV
        csv_filename = csv_files[0]
        with zip_ref.open(csv_filename) as f:
            # Decode bytes to string for pandas
            content = f.read().decode('utf-8')
            df = pd.read_csv(StringIO(content))
            
    logger.info(f"Loaded {len(df)} rows from {csv_filename}")
    return df

def run_lmm_simulation(df: pd.DataFrame) -> dict:
    """
    Runs a Linear Mixed Effects Model on the provided dataframe.
    Uses statsmodels MixedLM.
    Formula: rating ~ relationship * cue_intensity + (1|participant_id) + (1|stimulus_id)
    
    Returns coefficients and p-values for the interaction term.
    """
    try:
        # Ensure numeric types
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        df['cue_intensity'] = pd.to_numeric(df['cue_intensity'], errors='coerce')
        
        # Drop NaNs for modeling
        model_data = df.dropna(subset=['rating', 'cue_intensity', 'participant_id', 'stimulus_id', 'relationship'])
        
        if len(model_data) < 10:
            logger.warning("Dataset too small for LMM fitting")
            return {"estimate": 0.0, "p_value": 1.0, "z_value": 0.0}

        # Fit MixedLM
        # Note: statsmodels MixedLM uses 'groups' for the random effect grouping variable
        # We fit a model with random intercepts for participant and stimulus
        # Since MixedLM handles one grouping factor at a time, we might need to stack or use a workaround.
        # However, for power simulation, we often simulate the effect directly or use a simplified model
        # if the full random structure is too complex for a quick simulation.
        # Given the constraints, we will fit a model with participant random intercepts as the primary driver,
        # or use a fixed effect approximation if the full model fails.
        
        # Attempting a simplified LMM with participant as random effect
        # Formula: rating ~ relationship + cue_intensity + relationship:cue_intensity
        formula = "rating ~ relationship * cue_intensity"
        
        # Group by participant
        model = smf.mixedlm(formula, model_data, groups=model_data["participant_id"])
        result = model.fit(reml=False)
        
        # Extract interaction coefficient (relationship[T.acquaintance]:cue_intensity)
        # The column name depends on the reference level. We look for the interaction term.
        interaction_col = None
        for col in result.params.index:
            if "cue_intensity" in str(col) and "relationship" in str(col):
                interaction_col = col
                break
        
        if interaction_col is None:
            # Fallback: look for any interaction
            for col in result.params.index:
                if ":" in str(col) or "*" in str(col):
                    interaction_col = col
                    break

        if interaction_col:
            estimate = result.params[interaction_col]
            stderr = result.bse[interaction_col]
            z_value = estimate / stderr if stderr != 0 else 0.0
            p_value = 2 * (1 - statsmodels.stats.weightstats.ztost.ztost(estimate, stderr, 0, 0)[1]) # Approximation
            # Better p-value from result if available, but MixedLM summary is verbose.
            # Using a simple normal approximation for z-test
            from scipy.stats import norm
            p_value = 2 * (1 - norm.cdf(abs(z_value)))
            
            return {
                "estimate": float(estimate),
                "stderr": float(stderr),
                "z_value": float(z_value),
                "p_value": float(p_value),
                "significant": p_value < 0.05
            }
        else:
            logger.warning("Interaction term not found in model results")
            return {"estimate": 0.0, "p_value": 1.0, "z_value": 0.0}

    except Exception as e:
        logger.error(f"Error running LMM simulation: {e}", exc_info=True)
        return {"estimate": 0.0, "p_value": 1.0, "z_value": 0.0}

def estimate_power(simulation_results: list, alpha: float = 0.05) -> float:
    """
    Estimates power as the proportion of simulations where the interaction effect is significant.
    """
    if not simulation_results:
        return 0.0
    significant_count = sum(1 for r in simulation_results if r.get("significant", False))
    return significant_count / len(simulation_results)

def calculate_target_n(estimated_power: float, current_n: int, target_power: float = 0.80) -> int:
    """
    Heuristic calculation for target N based on current power estimate.
    If power < target, estimate required N by scaling.
    Power roughly scales with sqrt(N).
    N_target = N_current * (target_power / current_power)^2
    """
    if estimated_power >= target_power:
        return current_n
    
    if estimated_power <= 0:
        # If no power detected, assume we need a significant increase
        return current_n * 4 
        
    ratio = target_power / estimated_power
    # Avoid extreme scaling if power is very low
    if ratio > 10:
        ratio = 10
        
    target_n = int(current_n * (ratio ** 2))
    return max(target_n, current_n + 10) # Ensure some increase

def main():
    """
    Main entry point for T091.
    1. Load synthetic data from data/processed/synthetic_power_datasets.zip
    2. Run LMM simulation on the data (or multiple bootstrap samples if needed)
    3. Estimate power
    4. Calculate target N
    5. Save results to data/processed/power_analysis_results.json
    """
    logger.info("Starting Power Analysis Simulation (T091)")
    
    processed_dir = get_processed_data_dir()
    zip_path = processed_dir / "synthetic_power_datasets.zip"
    output_path = processed_dir / "power_analysis_results.json"
    
    # Load data
    try:
        df = load_synthetic_datasets(zip_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Run simulation
    # Since the synthetic dataset might already represent a full simulation run,
    # or we might need to bootstrap. The task says "Execute ... using the synthetic datasets".
    # If the dataset is a single large dataset, we run one LMM.
    # If it contains multiple simulation runs (unlikely for a single CSV), we iterate.
    # For robustness, we will run the LMM on the provided data.
    
    logger.info("Running LMM on synthetic data...")
    result = run_lmm_simulation(df)
    
    # Calculate power based on this single run? 
    # Strictly speaking, power is a probability over repeated sampling.
    # If the synthetic dataset represents ONE realization, we can't estimate power from one run.
    # However, T090b generated a dataset with N=60 and effect size 0.25.
    # We assume the 'synthetic_power_datasets.zip' might contain multiple bootstrap samples 
    # OR we treat the single run as the basis for a simplified power check.
    # Given the task description "Execute ... using the synthetic datasets to produce ...",
    # and the verification "estimated_power >= 0.80", we must derive a power estimate.
    
    # Strategy: If the dataset is large enough, we can bootstrap.
    # Or, if the dataset is a collection of simulation runs (e.g. 1000 rows where each row is a trial),
    # we run one LMM. If the p-value is significant, we might infer power is high for this N.
    # But to be precise: Power is the proportion of significant tests in repeated experiments.
    # If we only have one dataset, we cannot calculate empirical power.
    # ALTERNATIVE: The 'synthetic_power_datasets.zip' might be a collection of datasets.
    # Let's assume the zip contains a CSV where we can perform bootstrapping to estimate power.
    
    # Bootstrapping approach for power estimation from a single dataset:
    # Resample with replacement N times, run LMM, check significance.
    num_bootstrap = 100
    simulation_results = []
    
    logger.info(f"Performing {num_bootstrap} bootstrap iterations for power estimation...")
    
    for i in range(num_bootstrap):
        # Resample participants
        unique_participants = df['participant_id'].unique()
        sampled_participants = np.random.choice(unique_participants, size=len(unique_participants), replace=True)
        bootstrap_df = df[df['participant_id'].isin(sampled_participants)]
        
        if len(bootstrap_df) < 10:
            continue
            
        res = run_lmm_simulation(bootstrap_df)
        simulation_results.append(res)
        
    estimated_power = estimate_power(simulation_results)
    current_n = len(df['participant_id'].unique())
    target_n = calculate_target_n(estimated_power, current_n)
    
    logger.info(f"Estimated Power: {estimated_power:.2f}")
    logger.info(f"Target N for 0.80 power: {target_n}")
    
    # Prepare output
    output_data = {
        "estimated_power": estimated_power,
        "target_N": target_n,
        "method": "Bootstrap LMM (statsmodels MixedLM)",
        "current_N": current_n,
        "simulation_runs": num_bootstrap,
        "alpha": 0.05,
        "interaction_estimate_mean": np.mean([r['estimate'] for r in simulation_results]),
        "interaction_p_mean": np.mean([r['p_value'] for r in simulation_results])
    }
    
    # Save to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    logger.info(f"Power analysis results saved to {output_path}")
    print(json.dumps(output_data, indent=2))

if __name__ == "__main__":
    main()
