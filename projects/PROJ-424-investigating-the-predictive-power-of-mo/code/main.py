import argparse
import logging
import sys
import time
import json
import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import (
    Solvent, 
    SIMULATION_CONFIG, 
    ANALYSIS_CONFIG, 
    NIST_REFS_PATH, 
    MANIFEST_PATH,
    DATA_PROCESSED_DIR,
    DATA_INTERIM_DIR
)
from utils.logging import setup_logger, get_logger
from utils.data_fetcher import validate_nist_refs
from simulation.topology import generate_topology
from simulation.runner import run_simulation
from analysis.msd import analyze_msd, save_analysis_results
from analysis.sensitivity import run_sensitivity_sweep, save_sensitivity_report
from analysis.bootstrap import perform_bootstrap, save_bootstrap_stats
from reporting.plots import generate_timescale_accuracy_plot, generate_multi_solvent_comparison
from reporting.tables import generate_summary_table

logger = get_logger(__name__)

def load_nist_references() -> Dict[str, float]:
    """Load NIST reference diffusion coefficients."""
    validate_nist_refs()
    
    with open(NIST_REFS_PATH, 'r') as f:
        data = json.load(f)
    
    refs = {}
    for solvent_name, info in data['solvents'].items():
        refs[solvent_name] = info['value']
    
    return refs

def calculate_mae(simulated: float, experimental: float) -> float:
    """Calculate Mean Absolute Error."""
    return abs(simulated - experimental)

def run_single_solvent_pipeline(
    solvent: Solvent, 
    timescale: float, 
    full_batch: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Run the full pipeline for a single solvent and timescale.
    Returns a dictionary with results or None if skipped/failed.
    """
    start_time = time.time()
    solvent_name = solvent.value
    logger.info(f"Starting pipeline for {solvent_name} at {timescale}ns")

    # 1. Generate Topology
    logger.info(f"Generating topology for {solvent_name}...")
    try:
        topology_files = generate_topology(solvent, SIMULATION_CONFIG)
    except Exception as e:
        logger.error(f"Failed to generate topology: {e}")
        return None

    # 2. Run Simulation
    logger.info(f"Running simulation for {solvent_name}...")
    try:
        sim_result = run_simulation(
            solvent, 
            timescale, 
            SIMULATION_CONFIG,
            topology_files
        )
        if not sim_result.success:
            logger.warning(f"Simulation failed or flagged as invalid for {solvent_name}. Skipping.")
            return None
    except Exception as e:
        logger.error(f"Simulation execution failed: {e}")
        return None

    # 3. Analyze MSD
    logger.info(f"Analyzing MSD for {solvent_name}...")
    try:
        msd_result = analyze_msd(
            sim_result.trajectory_path,
            SIMULATION_CONFIG.scaling_factors[solvent],
            ANALYSIS_CONFIG.r_squared_threshold
        )
        
        if not msd_result.is_valid:
            logger.warning(f"MSD linearity validation failed for {solvent_name}. Skipping.")
            return None
    except Exception as e:
        logger.error(f"MSD analysis failed: {e}")
        return None

    # 4. Sensitivity Analysis (if not full batch or specifically requested)
    sensitivity_report = None
    if not full_batch:
        logger.info(f"Running sensitivity analysis for {solvent_name}...")
        try:
            sensitivity_report = run_sensitivity_sweep(
                sim_result.trajectory_path,
                SIMULATION_CONFIG.scaling_factors[solvent],
                ANALYSIS_CONFIG.sensitivity_start_fractions,
                ANALYSIS_CONFIG.r_squared_threshold
            )
            save_sensitivity_report(sensitivity_report, solvent_name, timescale)
        except Exception as e:
            logger.warning(f"Sensitivity analysis failed: {e}")
            # Continue even if sensitivity fails

    # 5. Calculate MAE
    nist_refs = load_nist_references()
    if solvent_name not in nist_refs:
        logger.warning(f"No NIST reference found for {solvent_name}. Skipping MAE calculation.")
        return None

    experimental_d = nist_refs[solvent_name]
    simulated_d = msd_result.diffusion_coefficient
    mae = calculate_mae(simulated_d, experimental_d)

    result = {
        "solvent": solvent_name,
        "timescale_ns": timescale,
        "experimental_d_m2s": experimental_d,
        "simulated_d_m2s": simulated_d,
        "mae": mae,
        "r_squared": msd_result.r_squared,
        "is_valid": msd_result.is_valid,
        "runtime_seconds": time.time() - start_time
    }

    logger.info(f"Completed {solvent_name} at {timescale}ns: D={simulated_d:.2e} m²/s, MAE={mae:.2e}")
    return result

def run_pipeline(full_batch: bool = False) -> List[Dict[str, Any]]:
    """
    Run the full batch analysis over all solvents and timescales.
    """
    logger.info("Starting full batch pipeline...")
    results = []
    
    solvents = [Solvent.WATER, Solvent.ETHANOL, Solvent.ACETONE]
    timescales = SIMULATION_CONFIG.time_steps

    for solvent in solvents:
        for timescale in timescales:
            result = run_single_solvent_pipeline(solvent, timescale, full_batch)
            if result:
                results.append(result)

    return results

def generate_final_plots(results: List[Dict[str, Any]]):
    """Generate final plots from the results."""
    logger.info("Generating final plots...")
    generate_timescale_accuracy_plot(results)
    generate_multi_solvent_comparison(results)

def run_bootstrap_analysis(results: List[Dict[str, Any]]):
    """Perform bootstrap analysis on the MAE distribution."""
    logger.info("Running bootstrap analysis...")
    if not results:
        logger.warning("No results to analyze for bootstrap.")
        return

    # Extract MAE values
    mae_values = [r['mae'] for r in results]
    
    # Run bootstrap
    bootstrap_result = perform_bootstrap(
        mae_values,
        target_iterations=ANALYSIS_CONFIG.bootstrap_target_iterations,
        time_limit_seconds=ANALYSIS_CONFIG.bootstrap_time_limit_seconds,
        min_iterations=ANALYSIS_CONFIG.bootstrap_min_iterations
    )
    
    save_bootstrap_stats(bootstrap_result)
    logger.info("Bootstrap analysis complete.")

def generate_summary_report(results: List[Dict[str, Any]]):
    """Generate the final summary table and report."""
    logger.info("Generating summary report...")
    if not results:
        logger.warning("No results to summarize.")
        return

    generate_summary_table(results)
    
    # Write final report markdown
    report_path = Path(DATA_PROCESSED_DIR) / "final_report.md"
    with open(report_path, 'w') as f:
        f.write("# Final Report: MD Predictive Power Analysis\n\n")
        f.write(f"Generated at: {datetime.utcnow().isoformat()}\n\n")
        f.write("## Summary Statistics\n")
        f.write(f"Total entries analyzed: {len(results)}\n\n")
        
        # Simple trend analysis
        water_results = [r for r in results if r['solvent'] == 'water']
        if len(water_results) >= 2:
            sorted_w = sorted(water_results, key=lambda x: x['timescale_ns'])
            early_mae = sorted_w[0]['mae']
            late_mae = sorted_w[-1]['mae']
            trend = "Improving" if late_mae < early_mae else "Worsening"
            f.write(f"## Water Trend Analysis\n")
            f.write(f"1ns MAE: {early_mae:.2e}\n")
            f.write(f"10ns MAE: {late_mae:.2e}\n")
            f.write(f"Trend: {trend}\n")

    logger.info(f"Final report written to {report_path}")

def main():
    parser = argparse.ArgumentParser(description="MD Diffusion Coefficient Prediction Pipeline")
    parser.add_argument("--full-batch", action="store_true", help="Run full batch analysis")
    parser.add_argument("--solvent", type=str, help="Specific solvent to run (water, ethanol, acetone)")
    parser.add_argument("--timescale", type=float, help="Specific timescale to run (ns)")
    parser.add_argument("--sensitivity", action="store_true", help="Run sensitivity analysis only")
    
    args = parser.parse_args()

    # Setup logging
    setup_logger()

    # Validate data
    try:
        validate_nist_refs()
    except Exception as e:
        logger.critical(f"Data validation failed: {e}")
        sys.exit(1)

    if args.solvent and args.timescale:
        # Single run
        solvent_enum = Solvent(args.solvent)
        result = run_single_solvent_pipeline(solvent_enum, args.timescale, full_batch=False)
        if not result:
            sys.exit(1)
    elif args.sensitivity and args.solvent and args.timescale:
        # Sensitivity run (handled inside single pipeline call usually, but explicit here)
        solvent_enum = Solvent(args.solvent)
        run_single_solvent_pipeline(solvent_enum, args.timescale, full_batch=False)
    else:
        # Full batch
        results = run_pipeline(full_batch=True)
        
        if results:
            generate_final_plots(results)
            run_bootstrap_analysis(results)
            generate_summary_report(results)
            logger.info("Pipeline completed successfully.")
        else:
            logger.warning("No results generated. Check logs for errors.")
            sys.exit(1)

if __name__ == "__main__":
    main()