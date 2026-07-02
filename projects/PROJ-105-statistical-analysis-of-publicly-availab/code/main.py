import os
import sys
import json
import time
import logging
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from preprocessing import main as preprocessing_main
from models import (
    estimate_x_min_ks,
    save_x_min_estimate,
    fit_all_base_distributions,
    fit_all_base_distributions_tail,
    fit_pareto_tail,
    calculate_tail_metrics,
    save_model_comparison,
    perform_vuong_test,
    save_vuong_test_results,
    compare_component_distributions
)
from utils import setup_logging, check_memory_limit, log_peak_memory
import config

logger = logging.getLogger(__name__)

def run_stage1():
    """Run Stage 1: Data acquisition and preprocessing."""
    logger.info("=== Stage 1: Data Acquisition and Preprocessing ===")
    preprocessing_main()
    logger.info("Stage 1 completed successfully.")

def run_stage2():
    """Run Stage 2: Model fitting and goodness-of-fit evaluation."""
    logger.info("=== Stage 2: Model Fitting and Evaluation ===")
    
    # Load cleaned data
    data_path = Path("data/processed/cleaned_delays.csv")
    if not data_path.exists():
        logger.error(f"Cleaned data not found at {data_path}. Run Stage 1 first.")
        sys.exit(1)

    import pandas as pd
    df = pd.read_csv(data_path)
    
    # Extract arrays
    total_delay = df['total_delay'].values
    arr_delay = df['ArrDelay'].values
    dep_delay = df['DepDelay'].values

    # Check memory
    check_memory_limit(config.MEMORY_LIMIT_GB)

    # Estimate x_min
    logger.info("Estimating x_min via KS minimization...")
    x_min = estimate_x_min_ks(total_delay)
    save_x_min_estimate(x_min)

    # Fit distributions on full data (excluding Pareto)
    logger.info("Fitting base distributions on full data...")
    full_fits = fit_all_base_distributions(total_delay, exclude_pareto=True)

    # Fit distributions on tail data
    logger.info("Fitting distributions on tail data...")
    tail_fits = fit_all_base_distributions_tail(total_delay, x_min, exclude_pareto=True)
    
    # Fit Pareto on tail data
    logger.info("Fitting Pareto on tail data...")
    try:
        pareto_dist, pareto_params = fit_pareto_tail(total_delay, x_min)
        tail_fits['pareto'] = (pareto_dist, pareto_params)
    except Exception as e:
        logger.warning(f"Pareto fitting failed: {e}")

    # Calculate metrics
    logger.info("Calculating model metrics...")
    metrics = calculate_tail_metrics(total_delay, tail_fits, x_min)
    save_model_comparison(metrics, x_min)

    # Perform Vuong test (best heavy-tail vs best short-tail)
    logger.info("Performing Vuong test...")
    if len(tail_fits) >= 2:
        # Simple heuristic: Pareto is heavy-tail, Exponential is short-tail
        if 'pareto' in tail_fits and 'expon' in tail_fits:
            vuong_results = perform_vuong_test(total_delay, tail_fits['pareto'][0], tail_fits['expon'][0], x_min)
            save_vuong_test_results(vuong_results, 'pareto', 'expon')
        else:
            logger.warning("Insufficient models for Vuong test")
    else:
        logger.warning("Not enough models fitted for Vuong test")

    # Component comparison (T028)
    logger.info("Comparing component distributions (T028)...")
    component_results = compare_component_distributions(total_delay, arr_delay, dep_delay)
    
    log_peak_memory()
    logger.info("Stage 2 completed successfully.")

def main():
    """Main entry point for the pipeline."""
    setup_logging()
    
    start_time = time.time()
    
    try:
        # Run Stage 1 if not already done
        if not Path("data/processed/cleaned_delays.csv").exists():
            run_stage1()
        
        # Run Stage 2
        run_stage2()
        
        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
