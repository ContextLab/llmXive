"""
Runner script to execute all robustness checks and aggregate the final metrics.

This script orchestrates the execution of:
1. Bootstrap analysis
2. Alpha sweep
3. Covariate adjustment
4. Binary model fit
5. Aggregation of all results into results/robustness_metrics.csv

It is designed to be run after the primary model (US1) has been executed.
"""
import sys
from pathlib import Path
from logging_config import setup_logging, get_logger
from robustness import run_all_robustness_checks
from binary_model import run_binary_model_pipeline
from aggregate_robustness import aggregate_robustness_metrics

def main():
    """
    Main entry point for the robustness analysis pipeline.
    """
    setup_logging()
    logger = get_logger()
    logger.info("Starting Robustness Analysis Pipeline...")
    
    try:
        # 1. Run all robustness checks (bootstrap, alpha sweep, covariate)
        # This function is expected to save results to results/bootstrap_results.csv,
        # results/alpha_sweep.csv, and results/covariate_adjustment.csv
        logger.info("Running robustness checks (bootstrap, alpha sweep, covariate)...")
        run_all_robustness_checks()
        
        # 2. Run binary model fit
        # This function is expected to save results to results/binary_model.csv
        logger.info("Running binary model fit...")
        run_binary_model_pipeline()
        
        # 3. Aggregate all results
        logger.info("Aggregating robustness metrics...")
        output_path = aggregate_robustness_metrics()
        
        if output_path:
            logger.info(f"Pipeline completed successfully. Output: {output_path}")
            return 0
        else:
            logger.error("Pipeline failed to generate aggregated output.")
            return 1
            
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())