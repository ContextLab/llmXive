import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

from config import get_config, verify_config
from utils.logging_config import configure_root_logger, log_info_with_context, log_error_with_context

# Import pipeline steps
from data_ingestion import load_oqmd_data, filter_valid_entries, save_processed_data
from feature_encoder import encode_dataframe, save_encoded_data
from model_training import run_training_pipeline
from model_validation import generate_validation_report, save_validation_report
from cluster_analysis import run_sensitivity_analysis, save_results as save_cluster_results
from pareto_optimization import run_nsgaII, save_results as save_pareto_results
from metrics_calculation import calculate_dominance_metrics, main as calc_metrics_main

logger = logging.getLogger(__name__)

def run_ingestion_step():
    """Runs the data ingestion step."""
    log_info_with_context("Starting data ingestion", context="main")
    config = get_config()
    
    try:
        df = load_oqmd_data()
        valid_df = filter_valid_entries(df)
        
        if len(valid_df) < 500:
            log_info_with_context(
                f"Insufficient data for statistical analysis (N < 500). Found {len(valid_df)} rows.",
                context="main"
            )
        
        output_path = os.path.join(config["processed_dir"], "encoded_alloys.csv")
        save_processed_data(valid_df, output_path)
        log_info_with_context(f"Ingestion complete. Output: {output_path}", context="main")
        return valid_df
    except Exception as e:
        log_error_with_context(f"Ingestion failed: {str(e)}", context="main")
        raise

def run_encoding_step(input_df):
    """Runs the feature encoding step."""
    log_info_with_context("Starting feature encoding", context="main")
    
    try:
        encoded_df = encode_dataframe(input_df)
        output_path = os.path.join(get_config()["processed_dir"], "encoded_alloys.csv")
        save_encoded_data(encoded_df, output_path)
        log_info_with_context(f"Encoding complete. Output: {output_path}", context="main")
        return encoded_df
    except Exception as e:
        log_error_with_context(f"Encoding failed: {str(e)}", context="main")
        raise

def run_training_step(encoded_df):
    """Runs the model training step."""
    log_info_with_context("Starting model training", context="main")
    try:
        metrics, models = run_training_pipeline(encoded_df)
        log_info_with_context("Training complete", context="main")
        return metrics, models
    except Exception as e:
        log_error_with_context(f"Training failed: {str(e)}", context="main")
        raise

def run_validation_step(models, encoded_df):
    """Runs the model validation step."""
    log_info_with_context("Starting model validation", context="main")
    try:
        report = generate_validation_report(models, encoded_df)
        output_path = os.path.join(get_config()["processed_dir"], "model_validation_report.json")
        save_validation_report(report, output_path)
        log_info_with_context(f"Validation complete. Output: {output_path}", context="main")
        return report
    except Exception as e:
        log_error_with_context(f"Validation failed: {str(e)}", context="main")
        raise

def run_pareto_step(models, encoded_df):
    """Runs the Pareto optimization step."""
    log_info_with_context("Starting Pareto optimization", context="main")
    try:
        frontier = run_nsgaII(models, encoded_df)
        output_path = os.path.join(get_config()["processed_dir"], "pareto_frontier.csv")
        save_pareto_results(frontier, output_path)
        log_info_with_context(f"Pareto optimization complete. Output: {output_path}", context="main")
        return frontier
    except Exception as e:
        log_error_with_context(f"Pareto optimization failed: {str(e)}", context="main")
        raise

def run_cluster_step(encoded_df):
    """Runs the cluster analysis step."""
    log_info_with_context("Starting cluster analysis", context="main")
    try:
        results = run_sensitivity_analysis(encoded_df)
        output_path = os.path.join(get_config()["processed_dir"], "sensitivity_analysis.csv")
        save_cluster_results(results, output_path)
        log_info_with_context(f"Cluster analysis complete. Output: {output_path}", context="main")
        return results
    except Exception as e:
        log_error_with_context(f"Cluster analysis failed: {str(e)}", context="main")
        raise

def run_metrics_step(frontier, encoded_df):
    """Runs the metrics calculation step."""
    log_info_with_context("Starting metrics calculation", context="main")
    try:
        metrics = calculate_dominance_metrics(frontier, encoded_df)
        output_path = os.path.join(get_config()["processed_dir"], "dominance_metrics.json")
        with open(output_path, 'w') as f:
            import json
            json.dump(metrics, f, indent=2)
        log_info_with_context(f"Metrics calculation complete. Output: {output_path}", context="main")
        return metrics
    except Exception as e:
        log_error_with_context(f"Metrics calculation failed: {str(e)}", context="main")
        raise

def main():
    """Main orchestration entry point."""
    configure_root_logger()
    config = get_config()
    verify_config(config)
    
    log_info_with_context("Starting Alloy Design Pipeline", context="main")
    start_time = datetime.now()
    
    try:
        # Step 1: Ingestion
        raw_df = run_ingestion_step()
        
        # Step 2: Encoding
        encoded_df = run_encoding_step(raw_df)
        
        # Step 3: Training
        metrics, models = run_training_step(encoded_df)
        
        # Step 4: Validation
        validation_report = run_validation_step(models, encoded_df)
        
        # Step 5: Pareto Optimization
        frontier = run_pareto_step(models, encoded_df)
        
        # Step 6: Cluster Analysis
        cluster_results = run_cluster_step(encoded_df)
        
        # Step 7: Metrics Calculation
        dominance_metrics = run_metrics_step(frontier, encoded_df)
        
        end_time = datetime.now()
        duration = end_time - start_time
        log_info_with_context(f"Pipeline completed successfully in {duration}", context="main")
        return 0
        
    except Exception as e:
        log_error_with_context(f"Pipeline failed: {str(e)}", context="main")
        return 1

if __name__ == "__main__":
    sys.exit(main())
