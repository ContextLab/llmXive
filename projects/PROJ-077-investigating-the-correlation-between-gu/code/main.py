"""
Main entry point for the Gut Microbiome and Cognitive Performance analysis pipeline.
Orchestrates the full pipeline: Configuration Validation -> Data Ingestion -> Diversity Analysis -> Correlation Analysis -> Visualization.
"""
import sys
import os
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from config import ensure_directories, RANDOM_SEED, SAMPLE_LIMIT
from config_validation import validate_configuration
from logging_config import get_logger, log_pipeline_start, log_pipeline_end, log_provenance

# Import data processing modules
from data_ingestion import run_data_ingestion
from diversity import calculate_diversity
from analysis import run_correlation_analysis, run_regression_analysis
from visualization import generate_plots

# Initialize logger
logger = get_logger(__name__)

def main():
    """
    Main pipeline execution function.
    """
    logger.info("=" * 80)
    log_pipeline_start("Gut Microbiome and Cognitive Performance Analysis")
    logger.info("=" * 80)
    
    try:
        # Step 1: Ensure directories exist
        logger.info("Step 1: Ensuring required directories exist...")
        ensure_directories()
        
        # Step 2: Validate configuration
        logger.info("Step 2: Validating configuration...")
        if not validate_configuration():
            logger.error("Configuration validation failed. Exiting.")
            sys.exit(1)
        
        # Step 3: Run data ingestion
        logger.info("Step 3: Running data ingestion and preprocessing...")
        cleaned_data_path = run_data_ingestion()
        if cleaned_data_path is None:
            logger.error("Data ingestion failed. Exiting.")
            sys.exit(1)
        
        # Step 4: Calculate diversity metrics
        logger.info("Step 4: Calculating alpha diversity metrics...")
        diversity_data_path = calculate_diversity(cleaned_data_path)
        if diversity_data_path is None:
            logger.error("Diversity calculation failed. Exiting.")
            sys.exit(1)
        
        # Step 5: Run correlation analysis
        logger.info("Step 5: Running correlation analysis...")
        correlation_results_path = run_correlation_analysis(diversity_data_path)
        if correlation_results_path is None:
            logger.error("Correlation analysis failed. Exiting.")
            sys.exit(1)
        
        # Step 6: Run regression analysis
        logger.info("Step 6: Running regression analysis...")
        regression_results_path = run_regression_analysis(diversity_data_path)
        if regression_results_path is None:
            logger.error("Regression analysis failed. Exiting.")
            sys.exit(1)
        
        # Step 7: Generate visualizations
        logger.info("Step 7: Generating visualizations...")
        plots_generated = generate_plots(diversity_data_path, correlation_results_path)
        if not plots_generated:
            logger.error("Visualization generation failed. Exiting.")
            sys.exit(1)
        
        # Step 8: Log completion
        logger.info("=" * 80)
        log_pipeline_end("Pipeline completed successfully")
        log_provenance("Pipeline Summary", {
            "cleaned_data": cleaned_data_path,
            "diversity_data": diversity_data_path,
            "correlation_results": correlation_results_path,
            "regression_results": regression_results_path,
            "plots_generated": True
        })
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {str(e)}")
        log_pipeline_end("Pipeline failed", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())
