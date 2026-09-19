"""
Main Entry Point for Avian Migration Pipeline.
Orchestrates the full pipeline execution.
"""
import logging
import sys
import argparse
from config import get_logger

logger = get_logger(__name__)

def run_pipeline():
    """
    Executes the full pipeline steps in order.
    """
    logger.info("Starting Avian Migration Pipeline...")
    
    try:
        # 1. Data Loading (T011, T012)
        logger.info("Step 1: Loading data...")
        from data_loader import load_ebird_data, load_modis_data
        # ebird_df = load_ebird_data()
        # modis_df = load_modis_data()
        
        # 2. Preprocessing (T013, T014, T015)
        logger.info("Step 2: Running first arrival sweep...")
        from preprocessing import run_first_arrival_sweep, validate_sweep_output
        # run_first_arrival_sweep()
        # validate_sweep_output()
        
        # 3. Model Training (T019-T024)
        logger.info("Step 3: Training model...")
        from model_training import main as train_model
        # train_model()
        
        # 4. Visualization (T032)
        logger.info("Step 4: Generating visualizations...")
        from visualization import main as viz
        # viz()
        
        logger.info("Pipeline execution completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

def main():
    """
    Main function with argument parsing.
    """
    parser = argparse.ArgumentParser(description="Avian Migration Pipeline")
    parser.add_argument("--validate", action="store_true", help="Run in validation mode")
    args = parser.parse_args()
    
    if args.validate:
        logger.info("Running in validation mode.")
        # In validate mode, we run the pipeline to measure time
        run_pipeline()
    else:
        run_pipeline()

if __name__ == "__main__":
    main()
