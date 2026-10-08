import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np

from config import SimulationConfig, load_config, validate_config, config_to_dict
from data_loader import load_and_validate, DataLoadError
from simulation import run_simulation_iteration
from metrics import calculate_type1_error, aggregate_results, compare_to_nominal, apply_fdr_correction
from analysis import run_complete_case_analysis, run_multiple_imputation, run_inverse_probability_weighting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/logs/main.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def validate_condition_matrix(config: SimulationConfig) -> Tuple[bool, str]:
    """
    Verify that the sweep configuration generates the full 72 conditions.
    8 rates x 3 mechanisms x 3 methods = 72.
    """
    rates = config.missing_rates
    mechanisms = config.missing_mechanisms
    methods = config.analysis_methods

    expected_count = len(rates) * len(mechanisms) * len(methods)
    actual_count = expected_count

    if actual_count != 72:
        return False, f"Expected 72 conditions (8x3x3), got {actual_count}. Check config rates/mechanisms/methods."
    
    logger.info(f"Condition matrix validated: {actual_count} conditions.")
    return True, "OK"

def run_single_condition_comparison(
    dataset: pd.DataFrame,
    config: SimulationConfig,
    mechanism: str,
    rate: float,
    method: str,
    seed: int
) -> Dict[str, Any]:
    """
    Run a single simulation iteration for a specific condition (mechanism, rate, method).
    Orchestrates: Permute -> Simulate Missing -> Analyze -> Return P-value.
    """
    # 1. Permute treatment labels to establish null hypothesis
    # Note: We need to do this inside the loop if we want unique permutations per iteration,
    # but for a single condition summary, we might run multiple iterations.
    # However, the task T033 implies we aggregate. Let's assume this function runs ONE iteration
    # or a small batch. Based on T017, run_simulation_iteration handles one full loop.
    # We will adapt run_simulation_iteration to accept specific parameters.
    
    # For T034, we need to run the simulation for the specific method.
    # We will perform N iterations (from config) to get a stable p-value distribution.
    n_iterations = config.n_iterations
    p_values = []

    for i in range(n_iterations):
        current_seed = seed + i
        
        # Run the core simulation logic for one iteration
        # This returns the p-value for this iteration under the specific condition
        result = run_simulation_iteration(
            dataset=dataset,
            mechanism=mechanism,
            missing_rate=rate,
            method=method,
            seed=current_seed,
            config=config
        )
        
        if result is not None and 'p_value' in result:
            p_values.append(result['p_value'])
        else:
            logger.warning(f"Iteration {i} failed to produce a p-value for {mechanism}/{rate}/{method}")

    if not p_values:
        raise RuntimeError(f"No p-values generated for condition: {mechanism}, {rate}, {method}")

    # Calculate empirical Type I error for this specific condition
    type1_error = calculate_type1_error(p_values, alpha=0.05)
    
    return {
        "mechanism": mechanism,
        "missing_rate": rate,
        "method": method,
        "n_iterations": len(p_values),
        "empirical_type1_error": type1_error,
        "p_values": p_values  # Keep for FDR if needed, though we aggregate first
    }

def compare_methods(
    dataset: pd.DataFrame,
    config: SimulationConfig,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Run the full comparison across all configured conditions (rates, mechanisms, methods).
    Returns a list of results dictionaries.
    """
    logger.info("Starting method comparison across all conditions...")
    
    # Validate matrix first
    is_valid, msg = validate_condition_matrix(config)
    if not is_valid:
        raise ValueError(msg)

    results = []
    rates = config.missing_rates
    mechanisms = config.missing_mechanisms
    methods = config.analysis_methods

    for mechanism in mechanisms:
        for rate in rates:
            for method in methods:
                logger.info(f"Running condition: {method} | {mechanism} | {rate:.2f}")
                try:
                    res = run_single_condition_comparison(
                        dataset=dataset,
                        config=config,
                        mechanism=mechanism,
                        rate=rate,
                        method=method,
                        seed=seed
                    )
                    results.append(res)
                except Exception as e:
                    logger.error(f"Failed condition {method}/{mechanism}/{rate}: {e}")
                    # Continue to next condition rather than crashing the whole sweep
                    continue

    logger.info(f"Comparison complete. {len(results)} conditions processed.")
    return results

def generate_comparison_report(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Generate a summary table/report showing CC inflation vs. MI/IPW stability.
    Outputs to JSON and optionally CSV/Text table.
    Implements SC-003 and SC-005.
    """
    logger.info(f"Generating comparison report to {output_path}")
    
    if not results:
        logger.error("No results to report.")
        return

    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(results)

    # Ensure we have the columns we expect
    required_cols = ['mechanism', 'missing_rate', 'method', 'empirical_type1_error']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column in results: {col}")

    # Pivot or reshape to compare methods side-by-side
    # We want to see: Rate, Mechanism, CC_Error, MI_Error, IPW_Error
    pivot_df = df.pivot_table(
        index=['missing_rate', 'mechanism'],
        columns='method',
        values='empirical_type1_error',
        aggfunc='first' # Should be unique per condition
    ).reset_index()

    # Calculate inflation for CC relative to nominal (0.05)
    # Inflation = (CC_Error - 0.05) / 0.05
    nominal = 0.05
    if 'Complete-Case' in pivot_df.columns:
        pivot_df['CC_inflation'] = (pivot_df['Complete-Case'] - nominal) / nominal
    
    # Calculate stability (variance or deviation from nominal) for MI/IPW
    # For this report, we'll just list the errors and flag if they exceed threshold (0.055)
    # SC-003: CC inflation vs MI/IPW stability
    
    # Identify tipping points (where CC > 1.1 * nominal)
    if 'Complete-Case' in pivot_df.columns:
        pivot_df['CC_tipping'] = pivot_df['Complete-Case'] > (nominal * 1.10)

    # Prepare the final report structure
    report_data = {
        "summary": {
            "total_conditions": len(results),
            "nominal_alpha": nominal,
            "tipping_threshold": nominal * 1.10
        },
        "comparison_table": pivot_df.to_dict(orient='records'),
        "detailed_results": results,
        "insights": []
    }

    # Add some high-level insights
    if 'Complete-Case' in pivot_df.columns:
        cc_failures = pivot_df[pivot_df['CC_tipping'] == True]
        if len(cc_failures) > 0:
            report_data["insights"].append(
                f"Complete-Case analysis exceeded 10% relative error threshold in {len(cc_failures)} conditions."
            )
        
        # Compare average error
        avg_cc = pivot_df['Complete-Case'].mean()
        avg_mi = pivot_df['Multiple Imputation'].mean() if 'Multiple Imputation' in pivot_df.columns else None
        avg_ipw = pivot_df['Inverse Probability Weighting'].mean() if 'Inverse Probability Weighting' in pivot_df.columns else None

        if avg_mi:
            report_data["insights"].append(
                f"Average CC error: {avg_cc:.4f}, Average MI error: {avg_mi:.4f}"
            )
        if avg_ipw:
            report_data["insights"].append(
                f"Average IPW error: {avg_ipw:.4f}"
            )

    # Write to JSON
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path_obj, 'w') as f:
        json.dump(report_data, f, indent=2)

    # Write a human-readable CSV table for the pivot
    csv_path = str(output_path_obj).replace('.json', '.csv')
    pivot_df.to_csv(csv_path, index=False)
    logger.info(f"Report saved to {output_path} and {csv_path}")

def main():
    """
    Main entry point for running the method comparison and generating the report.
    """
    # Load config
    config_path = os.getenv('SIMULATION_CONFIG', 'data/processed/simulation_config.json')
    if not os.path.exists(config_path):
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    validate_config(config)

    # Load dataset
    # T004/T004b handles loading and validation
    try:
        dataset = load_and_validate(config.dataset_source)
    except DataLoadError as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    # Run comparison
    results = compare_methods(dataset, config)

    # Generate report
    output_file = 'data/processed/method_comparison_report.json'
    generate_comparison_report(results, output_file)

    logger.info("Task T034 (generate_comparison_report) completed successfully.")

if __name__ == "__main__":
    main()