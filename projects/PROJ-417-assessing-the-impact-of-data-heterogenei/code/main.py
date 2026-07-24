"""
Main entry point for the llmXive automated science pipeline.

Orchestrates the full workflow:
1. Data Fetch (if not present)
2. Simulation Generation (with controlled heterogeneity)
3. Estimation (Fixed Effects, DL, REML)
4. Analysis (Bias, Coverage, I^2, Statistical Tests)
5. Reporting (Markdown report generation)

Usage:
    python code/main.py --seed 42 --levels 0.0 0.1 0.5 --replicates 10
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to ensure imports work when run as script
# Assuming this file is at code/main.py
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, get_logger, log_simulation_progress
from simulation.generator import (
    SimulationConfig,
    generate_synthetic_meta_analysis,
    validate_simulation_output,
    main as generate_main
)
from simulation.estimators import apply_estimator, EstimationResult
from analysis.metrics import (
    calculate_bias,
    calculate_coverage,
    calculate_i_squared,
    aggregate_metrics,
    MetricsResult
)
from analysis.stats import (
    exact_binomial_test,
    shapiro_wilk_test,
    bonferroni_correction,
    conditional_statistical_test,
    apply_anova,
    apply_kruskal_wallis
)
from reporting.report_gen import generate_report

logger = get_logger(__name__)

# Constants
DEFAULT_LEVELS = [0.0, 0.1, 0.5, 1.0, 2.0]
DEFAULT_REPLICATES = 500
DEFAULT_SEED = 42
OUTPUT_DIR = "data/results"
RAW_DATA_DIR = "data/raw"
SIMULATION_OUTPUT = "simulation_raw.json"
ESTIMATION_OUTPUT = "estimation_results.csv"
REPORT_OUTPUT = "report.md"
SENSITIVITY_OUTPUT = "sensitivity_sweep.csv"

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Orchestrate the meta-analysis heterogeneity impact pipeline."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})"
    )
    parser.add_argument(
        "--levels",
        type=float,
        nargs="+",
        default=DEFAULT_LEVELS,
        help=f"Heterogeneity levels (tau^2) to simulate (default: {DEFAULT_LEVELS})"
    )
    parser.add_argument(
        "--replicates",
        type=int,
        default=DEFAULT_REPLICATES,
        help=f"Number of replicates per level (default: {DEFAULT_REPLICATES})"
    )
    parser.add_argument(
        "--base-data",
        type=str,
        default="cochrane_base.csv",
        help="Base dataset filename in data/raw/ (default: cochrane_base.csv)"
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip simulation generation if output exists"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()

def ensure_directories():
    """Ensure output directories exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

def run_simulation(args: argparse.Namespace) -> Path:
    """Run the simulation generation phase."""
    logger.info(f"Starting simulation with seed={args.seed}, levels={args.levels}, replicates={args.replicates}")
    
    output_path = Path(OUTPUT_DIR) / SIMULATION_OUTPUT
    
    if args.skip_generation and output_path.exists():
        logger.info(f"Skipping generation. Output exists at {output_path}")
        return output_path

    config = SimulationConfig(
        seed=args.seed,
        tau2_levels=args.levels,
        replicates_per_level=args.replicates,
        base_data_file=args.base_data,
        base_data_dir=RAW_DATA_DIR
    )
    
    # Generate simulation
    simulation_result = generate_synthetic_meta_analysis(config)
    
    # Validate output
    if not validate_simulation_output(simulation_result):
        raise RuntimeError("Simulation output validation failed.")
    
    # Save output
    with open(output_path, 'w') as f:
        json.dump(simulation_result.to_dict(), f, indent=2)
    
    logger.info(f"Simulation complete. Output saved to {output_path}")
    return output_path

def run_estimation(simulation_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Run estimation phase on simulated data."""
    logger.info("Starting estimation phase...")
    
    results = []
    replicates = simulation_data.get("replicates", [])
    
    for i, replicate in enumerate(replicates):
        if i % 100 == 0:
            logger.info(f"Processing replicate {i}/{len(replicates)}")
        
        # Extract study data
        studies = replicate.get("studies", [])
        if not studies:
            logger.warning(f"Replicate {i} has no studies, skipping.")
            continue
        
        # Extract effect sizes and variances
        effects = [s["effect_size"] for s in studies]
        variances = [s["variance"] for s in studies]
        n_studies = len(studies)
        
        # Apply estimators
        estimators = ["fixed_effects", "dersimonian_laird", "reml"]
        
        for est_name in estimators:
            try:
                est_result = apply_estimator(effects, variances, estimator=est_name)
                
                # Calculate metrics
                true_effect = replicate.get("injected_true_effect", 0.0)
                injected_tau2 = replicate.get("injected_tau2", 0.0)
                
                bias = calculate_bias(est_result.pooled_estimate, true_effect)
                coverage = calculate_coverage(
                    est_result.pooled_estimate,
                    est_result.lower_ci,
                    est_result.upper_ci,
                    true_effect
                )
                i2 = calculate_i_squared(est_result.q_statistic, n_studies)
                
                # Determine reliability flag
                reliability_flag = "unreliable" if n_studies < 5 else "reliable"
                
                result_entry = {
                    "replicate_id": replicate.get("id", i),
                    "estimator": est_name,
                    "n_studies": n_studies,
                    "pooled_estimate": est_result.pooled_estimate,
                    "lower_ci": est_result.lower_ci,
                    "upper_ci": est_result.upper_ci,
                    "tau2_estimate": est_result.tau2_estimate,
                    "i_squared": i2,
                    "bias": bias,
                    "coverage": coverage,
                    "true_effect": true_effect,
                    "injected_tau2": injected_tau2,
                    "reliability_flag": reliability_flag,
                    "convergence_success": est_result.convergence_success
                }
                results.append(result_entry)
                
            except Exception as e:
                logger.error(f"Estimation failed for replicate {i}, estimator {est_name}: {e}")
                continue
    
    return results

def run_analysis(estimation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run statistical analysis phase."""
    logger.info("Starting analysis phase...")
    
    if not estimation_results:
        logger.warning("No estimation results to analyze.")
        return {}
    
    # Aggregate metrics
    aggregated = aggregate_metrics(estimation_results)
    
    # Perform statistical tests
    # Test coverage deviation using binomial test
    coverage_results = [r for r in estimation_results if r.get("coverage") is not None]
    if coverage_results:
        observed_coverage = sum(1 for r in coverage_results if r["coverage"] == 1.0)
        total = len(coverage_results)
        nominal_level = 0.95
        
        if total > 0:
            binom_result = exact_binomial_test(observed_coverage, total, nominal_level)
            aggregated["binomial_test"] = binom_result
    
    # Test normality of bias distribution for ANOVA/Kruskal-Wallis
    bias_values = [r["bias"] for r in estimation_results if r.get("bias") is not None]
    if len(bias_values) > 3:
        shapiro_result = shapiro_wilk_test(bias_values)
        aggregated["shapiro_wilk"] = shapiro_result
        
        # Conditional test selection
        test_result = conditional_statistical_test(
            bias_values, 
            group_col="estimator", 
            data=estimation_results
        )
        aggregated["group_comparison"] = test_result
    
    # Apply Bonferroni correction if multiple tests were run
    if "binomial_test" in aggregated and "group_comparison" in aggregated:
        p_values = [aggregated["binomial_test"].get("p_value", 1.0)]
        if "p_value" in aggregated["group_comparison"]:
            p_values.append(aggregated["group_comparison"]["p_value"])
        
        if len(p_values) > 1:
            corrected = bonferroni_correction(p_values)
            aggregated["bonferroni_correction"] = corrected
    
    return aggregated

def run_reporting(aggregated_metrics: Dict[str, Any], estimation_results: List[Dict[str, Any]]):
    """Generate final report."""
    logger.info("Generating report...")
    
    report_path = Path(OUTPUT_DIR) / REPORT_OUTPUT
    
    # Prepare data for report
    report_data = {
        "aggregated_metrics": aggregated_metrics,
        "estimation_results_count": len(estimation_results),
        "timestamp": "auto-generated"
    }
    
    generate_report(report_data, output_path=report_path)
    logger.info(f"Report generated at {report_path}")

def main():
    """Main orchestration function."""
    args = parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level, log_file=Path(OUTPUT_DIR) / "pipeline.log")
    
    logger.info("Starting meta-analysis heterogeneity pipeline...")
    
    try:
        # 1. Ensure directories
        ensure_directories()
        
        # 2. Run Simulation
        sim_path = run_simulation(args)
        
        # 3. Load simulation data
        with open(sim_path, 'r') as f:
            simulation_data = json.load(f)
        
        # 4. Run Estimation
        estimation_results = run_estimation(simulation_data)
        
        # 5. Save estimation results
        if estimation_results:
            import csv
            csv_path = Path(OUTPUT_DIR) / ESTIMATION_OUTPUT
            with open(csv_path, 'w', newline='') as f:
                if estimation_results:
                    writer = csv.DictWriter(f, fieldnames=estimation_results[0].keys())
                    writer.writeheader()
                    writer.writerows(estimation_results)
            logger.info(f"Estimation results saved to {csv_path}")
        
        # 6. Run Analysis
        aggregated_metrics = run_analysis(estimation_results)
        
        # 7. Generate Report
        run_reporting(aggregated_metrics, estimation_results)
        
        logger.info("Pipeline completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())