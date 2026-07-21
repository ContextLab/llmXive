import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path

from preprocessing import preprocess_flight_delays, save_summary_report, main as preprocessing_main
from data_loader import download_bts_data, main as data_loader_main
from models import (
    fit_all_base_distributions, fit_pareto_tail, calculate_tail_metrics,
    save_model_comparison, perform_vuong_test, save_vuong_test_results,
    compare_component_distributions, main as models_main
)
from diagnostics import (
    run_hill_stability_analysis, save_hill_results, perform_log_normal_discrimination,
    save_log_normal_test_results, perform_model_rejection, main as diagnostics_main
)
from validation import run_validation, main as validation_main
from config import TARGET_YEAR, MEMORY_LIMIT_GB
from utils import setup_logging, check_memory_limit, log_peak_memory

logger = logging.getLogger(__name__)

def load_json_safe(path: str) -> dict:
    """Load JSON file safely."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {path}: {e}")
        return {}

def run_stage1(year: int) -> dict:
    """Stage 1: Data Acquisition and Pre-processing."""
    logger.info("Executing Stage 1: Data Acquisition and Pre-processing")
    
    # Download data
    raw_output = download_bts_data(year=year, output_dir="data/raw")
    
    # Preprocess
    cleaned_output, summary = preprocess_flight_delays(raw_output)
    save_summary_report(summary, "data/results/summary_report.json")
    
    return {
        "cleaned_delays": cleaned_output,
        "summary": summary
    }

def run_stage2(cleaned_delays_path: str) -> dict:
    """Stage 2: Parametric Model Fitting and Goodness-of-Fit."""
    logger.info("Executing Stage 2: Model Fitting")
    
    # Load x_min estimate
    x_min_path = "data/results/x_min_estimate.json"
    x_min_data = load_json_safe(x_min_path)
    x_min = x_min_data.get("x_min", 10.0)
    
    # Fit models
    metrics = fit_all_base_distributions(cleaned_delays_path, x_min)
    save_model_comparison(metrics, "data/results/model_comparison.json")
    
    # Vuong test
    vuong_results = perform_vuong_test(cleaned_delays_path, x_min)
    save_vuong_test_results(vuong_results, "data/results/vuong_test_results.json")
    
    return metrics

def run_stage3(cleaned_delays_path: str) -> dict:
    """Stage 3: Heavy-Tail Diagnostics and Visualization."""
    logger.info("Executing Stage 3: Diagnostics")
    
    # Load x_min
    x_min_path = "data/results/x_min_estimate.json"
    x_min_data = load_json_safe(x_min_path)
    x_min = x_min_data.get("x_min", 10.0)
    
    # Hill stability
    import pandas as pd
    df = pd.read_csv(cleaned_delays_path)
    data = df['total_delay'].values
    tail_data = data[data >= x_min]
    
    hill_results = run_hill_stability_analysis(tail_data)
    save_hill_results(hill_results, "data/results/tail_index_estimate.json")
    
    # Log-Normal discrimination
    lognorm_results = perform_log_normal_discrimination(data, x_min)
    save_log_normal_test_results(lognorm_results, "data/results/log_normal_test.json")
    
    # Model rejection
    rejection_results = perform_model_rejection(data, x_min, "Pareto", {})
    Path("data/results/model_rejection.json").parent.mkdir(parents=True, exist_ok=True)
    with open("data/results/model_rejection.json", 'w') as f:
        json.dump(rejection_results, f, indent=2)
    
    return {
        "hill": hill_results,
        "log_normal": lognorm_results,
        "rejection": rejection_results
    }

def run_stage4() -> dict:
    """Stage 4: Final Validation and Reporting."""
    logger.info("Executing Stage 4: Validation")
    validation_results = run_validation()
    return validation_results

def main():
    """Main pipeline entry point."""
    parser = argparse.ArgumentParser(description="Flight Delay Analysis Pipeline")
    parser.add_argument("--input", required=True, help="Path to input CSV (for stages 2-4)")
    parser.add_argument("--output", required=True, help="Path to output CSV (for stage 1)")
    parser.add_argument("--summary", default="data/results/summary_report.json", help="Path to summary report")
    parser.add_argument("--year", type=int, help="Year for data download (stage 1 only)")
    
    args = parser.parse_args()
    
    setup_logging()
    logger.info("Starting Flight Delay Analysis Pipeline")
    
    start_time = time.time()
    
    try:
        if args.year:
            # Stage 1: Download and preprocess
            stage1_results = run_stage1(args.year)
            cleaned_path = stage1_results["cleaned_delays"]
        else:
            cleaned_path = args.input
        
        # Stage 2: Model fitting
        stage2_results = run_stage2(cleaned_path)
        
        # Stage 3: Diagnostics
        stage3_results = run_stage3(cleaned_path)
        
        # Stage 4: Validation
        stage4_results = run_stage4()
        
        # Compile final report
        final_report = {
            "runtime": time.time() - start_time,
            "stage1": stage1_results if args.year else None,
            "stage2": stage2_results,
            "stage3": stage3_results,
            "stage4": stage4_results
        }
        
        Path("data/results/final_report.json").parent.mkdir(parents=True, exist_ok=True)
        with open("data/results/final_report.json", 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Pipeline complete in {time.time() - start_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
