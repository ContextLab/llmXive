import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path

# Project imports
from config import get_bts_url
from data_loader import download_bts_data
from preprocessing import preprocess_flight_delays, save_summary_report
from models import (
    fit_all_base_distributions,
    fit_pareto_tail,
    calculate_tail_metrics,
    save_model_comparison,
    perform_vuong_test,
    save_vuong_test_results,
    compare_component_distributions
)
from diagnostics import (
    estimate_hill_index,
    compute_hill_stability_curve,
    find_optimal_k_stability,
    calculate_hill_confidence_interval,
    run_hill_stability_analysis,
    save_hill_results,
    calculate_r2_on_tail,
    perform_tail_ks_test,
    check_model_rejection,
    update_model_comparison
)
from validation import run_validation
from utils import setup_logging, check_memory_limit, log_peak_memory, PipelineError
from visualization import plot_loglog_survival, plot_qq_plot, save_r2_results

logger = logging.getLogger(__name__)

def load_json_safe(path: str) -> dict:
    """Load a JSON file safely."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return {}

def run_stage1(args):
    """Stage 1: Data Acquisition and Pre-processing."""
    logger.info("Executing Stage 1: Data Acquisition and Pre-processing")
    
    # Determine input/output paths
    if hasattr(args, 'input') and args.input:
        input_path = args.input
    else:
        # Fallback to download if no input provided
        year = getattr(args, 'year', 2022)
        output_dir = "data/raw"
        os.makedirs(output_dir, exist_ok=True)
        input_path = download_bts_data(year=year, output_dir=output_dir)
    
    output_csv = getattr(args, 'output', 'data/processed/cleaned_delays.csv')
    summary_path = getattr(args, 'summary', 'data/results/summary_report.json')
    
    # Preprocess
    df = preprocess_flight_delays(input_path)
    
    # Save outputs
    df.to_csv(output_csv, index=False)
    save_summary_report(df, summary_path)
    
    logger.info(f"Stage 1 complete: {len(df)} records saved to {output_csv}")
    return output_csv

def run_stage2(args, cleaned_csv_path):
    """Stage 2: Model Fitting and Goodness-of-Fit Evaluation."""
    logger.info("Executing Stage 2: Model Fitting and Goodness-of-Fit Evaluation")
    
    # Load data
    import pandas as pd
    df = pd.read_csv(cleaned_csv_path)
    delays = df['total_delay'].values
    
    # Fit models on full data
    full_metrics = fit_all_base_distributions(delays)
    
    # Estimate x_min
    x_min_data = load_json_safe('data/results/x_min_estimate.json')
    x_min = x_min_data.get('x_min', 0) if x_min_data else 0
    if x_min == 0:
        # Fallback if T026 failed
        x_min = 10.0
        logger.warning(f"x_min not found, using fallback: {x_min}")
    
    # Filter tail
    tail_mask = delays >= x_min
    tail_data = delays[tail_mask]
    
    if len(tail_data) == 0:
        raise ValueError("No data points in tail (delay >= x_min)")
    
    # Fit tail models
    tail_metrics = fit_all_base_distributions(tail_data, name_suffix="_tail")
    
    # Fit Pareto
    pareto_metrics = fit_pareto_tail(tail_data, x_min)
    
    # Combine metrics
    all_metrics = {**full_metrics, **tail_metrics, **pareto_metrics}
    
    # Calculate metrics
    metrics_with_stats = calculate_tail_metrics(all_metrics, tail_data, x_min)
    
    # Save model comparison
    save_model_comparison(metrics_with_stats, 'data/results/model_comparison.json')
    
    # Perform Vuong test
    vuong_results = perform_vuong_test(metrics_with_stats, tail_data)
    save_vuong_test_results(vuong_results, 'data/results/vuong_test_results.json')
    
    logger.info("Stage 2 complete: Models fitted and compared")
    return metrics_with_stats

def run_stage3(args, metrics_with_stats):
    """Stage 3: Diagnostics and Validation (FR-015 Logic)."""
    logger.info("Executing Stage 3: Heavy-Tail Diagnostics and Validation")
    
    # Load data for diagnostics
    import pandas as pd
    df = pd.read_csv('data/processed/cleaned_delays.csv')
    delays = df['total_delay'].values
    
    # Load x_min
    x_min_data = load_json_safe('data/results/x_min_estimate.json')
    x_min = x_min_data.get('x_min', 10.0) if x_min_data else 10.0
    
    # Filter tail
    tail_mask = delays >= x_min
    tail_data = delays[tail_mask]
    
    if len(tail_data) == 0:
        raise ValueError("No data points in tail for diagnostics")
    
    # 1. Hill Estimator Stability Analysis
    logger.info("Running Hill stability analysis...")
    hill_results = run_hill_stability_analysis(tail_data, x_min)
    save_hill_results(hill_results, 'data/results/tail_index_estimate.json')
    
    # Save stability curve
    import pandas as pd
    stability_df = pd.DataFrame(hill_results['stability_curve'])
    stability_df.to_csv('data/results/stability_curve.csv', index=False)
    
    # 2. R² Calculation on Log-Log Survival
    logger.info("Calculating R² on tail survival plot...")
    r2_value, r2_data = calculate_r2_on_tail(tail_data, x_min)
    save_r2_results(r2_data, 'data/results/r2_results.json')
    
    # 3. Perform Tail KS Test
    logger.info("Performing Tail KS test...")
    ks_results = perform_tail_ks_test(tail_data, x_min, metrics_with_stats)
    # The function perform_tail_ks_test is expected to write tail_ks.json internally
    # If not, we ensure it here based on the contract
    if not os.path.exists('data/results/tail_ks.json'):
        with open('data/results/tail_ks.json', 'w') as f:
            json.dump(ks_results, f, indent=2)
    
    # 4. Model Rejection Logic (FR-015)
    logger.info("Checking model rejection criteria (R² < 0.95 or Hill unstable)...")
    rejection_result = check_model_rejection(
        r2_value, 
        hill_results, 
        metrics_with_stats,
        'data/results/model_comparison.json'
    )
    
    # Save rejection report
    with open('data/results/model_rejection.json', 'w') as f:
        json.dump(rejection_result, f, indent=2)
    
    # 5. Update Model Comparison with Rejection Status
    update_model_comparison('data/results/model_comparison.json', rejection_result)
    
    # 6. Visualization (Optional but good for debug)
    try:
        plot_loglog_survival(tail_data, x_min, metrics_with_stats)
        logger.info("Log-log survival plot saved to figures/survival_plot.png")
    except Exception as e:
        logger.warning(f"Could not generate survival plot: {e}")
    
    logger.info("Stage 3 complete: Diagnostics and validation finished")
    return rejection_result

def run_stage4(args):
    """Stage 4: Final Compilation and Validation."""
    logger.info("Executing Stage 4: Final Compilation and Validation")
    
    # Run validation checks
    validation_status = run_validation()
    
    # Compile final summary
    final_summary = {
        "status": "complete",
        "validation": validation_status,
        "artifacts": {
            "cleaned_data": "data/processed/cleaned_delays.csv",
            "summary_report": "data/results/summary_report.json",
            "model_comparison": "data/results/model_comparison.json",
            "vuong_test": "data/results/vuong_test_results.json",
            "x_min_estimate": "data/results/x_min_estimate.json",
            "tail_index": "data/results/tail_index_estimate.json",
            "stability_curve": "data/results/stability_curve.csv",
            "model_rejection": "data/results/model_rejection.json",
            "tail_ks": "data/results/tail_ks.json"
        }
    }
    
    with open('data/results/final_summary.json', 'w') as f:
        json.dump(final_summary, f, indent=2)
    
    logger.info("Stage 4 complete: Final summary generated")
    return final_summary

def main():
    parser = argparse.ArgumentParser(description="Flight Delay Analysis Pipeline")
    parser.add_argument('--year', type=int, help='Year for data download (if no input provided)')
    parser.add_argument('--input', type=str, help='Input CSV path (overrides --year)')
    parser.add_argument('--output', type=str, help='Output CSV path for cleaned data')
    parser.add_argument('--summary', type=str, help='Path for summary report JSON')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger.info("Starting Flight Delay Analysis Pipeline")
    
    start_time = time.time()
    
    try:
        # Stage 1
        cleaned_path = run_stage1(args)
        
        # Stage 2
        metrics = run_stage2(args, cleaned_path)
        
        # Stage 3 (T039 Implementation)
        run_stage3(args, metrics)
        
        # Stage 4
        run_stage4(args)
        
        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds")
        
    except PipelineError as e:
        logger.error(f"Pipeline Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()