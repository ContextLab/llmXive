"""
Helper script to run the specific pipeline steps required to generate
the missing artifacts for T023 and subsequent tasks.
This script is invoked by the run-book to ensure data flows correctly.
"""
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from code.simulation.test_runner import main as simulation_main
from code.analysis.aggregator import main as aggregator_main
from code.analysis.threshold_finder import main as threshold_main
from code.visualization.plotter import main as plotter_main
from code.analysis.validator import main as validator_main
from code.analysis.bootstrapper import main as bootstrapper_main
from code.analysis.validation_metrics import main as metrics_main
from code.analysis.report_generator import main as report_main

def run_step(name, func):
    print(f"--- Running {name} ---")
    try:
        func()
        print(f"--- {name} completed successfully ---\n")
        return True
    except Exception as e:
        print(f"--- {name} FAILED: {e} ---\n")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("Starting Pipeline Execution for PROJ-341...")

    # 1. Simulation (Generates p_values_raw.csv)
    # Note: In a full run, this might take hours. We assume it's been run or
    # we run a small subset. For this script, we call the main which handles args.
    # To make this script runnable for T023 specifically, we assume T018 (aggregator)
    # has run or we run it here.
    
    # The execution log showed T018 (aggregator) was not invoked.
    # We must ensure the flow: Simulation -> Aggregation -> Thresholds.
    
    # Since we are fixing T023 (Thresholds), we assume p_values_raw.csv exists.
    # If not, we might need to run a small simulation here.
    # However, the execution log showed the main failure was ImportError in validator.
    # We will assume the simulation data exists if the import error is fixed.
    
    # Step A: Aggregation (T018) - creates error_rates_summary.csv
    success = run_step("Aggregation (T018)", aggregator_main)
    if not success:
        print("Aggregation failed. Thresholds cannot be calculated.")
        return 1

    # Step B: Thresholds (T023) - creates thresholds.json
    success = run_step("Threshold Calculation (T023)", threshold_main)
    if not success:
        print("Threshold calculation failed.")
        return 1

    # Step C: Plots (T024-T027) - creates figures
    success = run_step("Plotting (T024-T027)", plotter_main)
    if not success:
        print("Plotting failed (non-fatal for T023).")
    
    # Step D: Validation (T029-T031) - creates real_data_pvalues.csv
    # Only if imports are fixed in validator.py
    success = run_step("Validation Data Download & Run (T029-T031)", validator_main)
    if not success:
        print("Validation failed (non-fatal for T023).")

    # Step E: Bootstrapping (T032) - creates real_data_power.json
    success = run_step("Bootstrapping (T032)", bootstrapper_main)
    if not success:
        print("Bootstrapping failed (non-fatal for T023).")

    # Step F: Metrics (T034) - creates validation_metrics.json
    success = run_step("Validation Metrics (T034)", metrics_main)
    if not success:
        print("Validation Metrics failed (non-fatal for T023).")

    # Step G: Report (T033)
    success = run_step("Report Generation (T033)", report_main)
    if not success:
        print("Report Generation failed (non-fatal for T023).")

    print("Pipeline execution finished.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
