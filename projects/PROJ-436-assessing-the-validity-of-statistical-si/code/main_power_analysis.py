"""
main_power_analysis.py

Executes the alternative hypothesis sweep (Power Analysis) to satisfy SC-004.
Runs simulations across multiple missingness rates and mechanisms with an injected
treatment effect (Cohen's d=0.5) to calculate empirical statistical power.

Output: data/processed/power_results.json
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import SimulationConfig, load_config, validate_config, config_to_dict
from simulation import (
    permute_treatment_labels,
    simulate_mcar,
    simulate_mar,
    simulate_mnar,
    simulate_alternative_hypothesis,
    run_simulation_iteration
)
from metrics import calculate_power, aggregate_results
from data_loader import load_and_validate
from configure_sweep_rates import configure_sweep_rates

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'logs' / 'power_analysis.log')
    ]
)
logger = logging.getLogger(__name__)

def run_power_sweep(
    dataset_id: int,
    mechanisms: List[str],
    rates: List[float],
    effect_size: float = 0.5,
    n_iterations: int = 500,
    seed: int = 42,
    outcome_type: str = 'continuous'
) -> Dict[str, Any]:
    """
    Runs the full power analysis sweep.

    Args:
        dataset_id: OpenML ID for the RCT dataset.
        mechanisms: List of missingness mechanisms ('mcar', 'mar', 'mnar').
        rates: List of missingness rates to test.
        effect_size: Cohen's d for the alternative hypothesis (default 0.5).
        n_iterations: Number of simulation iterations per condition.
        seed: Random seed for reproducibility.
        outcome_type: Type of outcome ('continuous' or 'binary').

    Returns:
        Dictionary containing the full results structure.
    """
    logger.info(f"Starting Power Analysis Sweep for dataset {dataset_id}")
    logger.info(f"Mechanisms: {mechanisms}, Rates: {rates}, Effect Size: {effect_size}")

    # Load and validate the real dataset
    try:
        df_raw = load_and_validate(dataset_id)
        logger.info(f"Loaded dataset {dataset_id} with shape {df_raw.shape}")
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        raise

    results = {
        "config": {
            "dataset_id": dataset_id,
            "effect_size": effect_size,
            "n_iterations": n_iterations,
            "seed": seed,
            "mechanisms": mechanisms,
            "rates": rates
        },
        "conditions": []
    }

    np.random.seed(seed)

    for mechanism in mechanisms:
        for rate in rates:
            condition_id = f"{mechanism}_{rate}"
            logger.info(f"Running condition: {condition_id} (Mechanism={mechanism}, Rate={rate})")

            # 1. Establish Null (Permute Treatment) - This is standard for Type I,
            #    BUT for Power (Alternative Hypothesis), we do NOT permute treatment labels.
            #    We keep the original treatment labels to preserve the true effect,
            #    then inject the effect if necessary (though the dataset should ideally have it).
            #    However, the task T019c defines `simulate_alternative_hypothesis` which injects effect.
            #    To measure power, we need a known effect. If the dataset is real, it has some effect.
            #    To standardize, we inject a known effect size (d=0.5) into the outcome variable
            #    relative to the treatment group, then simulate missingness and test.

            # Step A: Prepare data for simulation
            # We create a copy to avoid modifying the original
            df_sim = df_raw.copy()

            # Step B: Inject Alternative Hypothesis (Effect Size d=0.5)
            # This ensures we are measuring power against a specific, known effect.
            # T019c implementation handles this logic.
            df_sim = simulate_alternative_hypothesis(df_sim, effect_size=effect_size)

            # Step C: Simulate Missingness
            if mechanism == 'mcar':
                df_missing = simulate_mcar(df_sim, missing_rate=rate)
            elif mechanism == 'mar':
                df_missing = simulate_mar(df_sim, missing_rate=rate)
            elif mechanism == 'mnar':
                df_missing = simulate_mnar(df_sim, missing_rate=rate)
            else:
                raise ValueError(f"Unknown mechanism: {mechanism}")

            # Step D: Run Analysis (Iterate)
            # Since we are measuring Power (rejecting null when alternative is true),
            # we run the simulation loop.
            # Note: `run_simulation_iteration` expects a config and data.
            # We need to adapt the loop to collect p-values for power calculation.

            p_values = []
            for i in range(n_iterations):
                # For power, we do NOT permute treatment labels.
                # We use the data with the injected effect.
                # We simulate missingness again per iteration to account for missingness variance?
                # Actually, the standard approach for Power in this context:
                # 1. Fix the data with injected effect.
                # 2. For each iteration:
                #    a. Simulate missingness (MCAR/MAR/MNAR)
                #    b. Run statistical test
                #    c. Store p-value

                # Re-simulate missingness for each iteration
                if mechanism == 'mcar':
                    df_iter = simulate_mcar(df_sim, missing_rate=rate)
                elif mechanism == 'mar':
                    df_iter = simulate_mar(df_sim, missing_rate=rate)
                elif mechanism == 'mnar':
                    df_iter = simulate_mnar(df_sim, missing_rate=rate)

                # Run test
                # We assume the test function returns a p-value
                # We need to ensure we are testing the difference in means (t-test or wilcoxon)
                # The `run_simulation_iteration` might be designed for Type I (permuted).
                # Let's manually implement the loop here to ensure correctness for Power.

                outcome_col = 'outcome' # Assuming standard name from data_loader
                treatment_col = 'treatment' # Assuming standard name

                # Check for missingness and drop (Complete Case)
                valid_rows = df_iter.dropna(subset=[outcome_col, treatment_col])
                if len(valid_rows) < 10:
                    p_values.append(1.0) # No data, fail to reject
                    continue

                group_0 = valid_rows[valid_rows[treatment_col] == 0][outcome_col]
                group_1 = valid_rows[valid_rows[treatment_col] == 1][outcome_col]

                if outcome_type == 'binary':
                    stat, p_val = stats.mannwhitneyu(group_0, group_1, alternative='two-sided')
                else:
                    # Check normality? For simplicity in power analysis loop, use t-test if N is large
                    # or fallback to non-parametric if needed.
                    # The `select_test_statistic` from metrics can help.
                    stat, p_val = stats.ttest_ind(group_0, group_1)

                p_values.append(p_val)

            # Calculate Power
            # Power = P(p < alpha | H1 is true)
            alpha = 0.05
            power = sum(1 for p in p_values if p < alpha) / len(p_values)

            condition_result = {
                "mechanism": mechanism,
                "rate": rate,
                "n_iterations": n_iterations,
                "effect_size_injected": effect_size,
                "power_estimate": power,
                "p_value_distribution": p_values # Optional: store full dist for debugging
            }

            results["conditions"].append(condition_result)
            logger.info(f"  -> Power Estimate: {power:.4f}")

    return results

def main():
    """
    Main entry point for the power analysis script.
    Loads configuration, runs the sweep, and saves results.
    """
    logger.info("Initializing Power Analysis Script")

    # Define sweep parameters
    # These can be loaded from a config file or hardcoded here for the task
    dataset_id = 436 # Example RCT ID
    mechanisms = ['mcar', 'mar', 'mnar']
    rates = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5] # 0.0 is baseline
    effect_size = 0.5
    n_iterations = 500
    seed = 42
    outcome_type = 'continuous'

    # Ensure output directory exists
    output_dir = project_root / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'power_results.json'

    try:
        results = run_power_sweep(
            dataset_id=dataset_id,
            mechanisms=mechanisms,
            rates=rates,
            effect_size=effect_size,
            n_iterations=n_iterations,
            seed=seed,
            outcome_type=outcome_type
        )

        # Save results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Power analysis complete. Results saved to {output_path}")

    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()