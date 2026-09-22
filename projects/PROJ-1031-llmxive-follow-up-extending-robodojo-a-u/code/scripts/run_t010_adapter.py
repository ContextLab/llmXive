"""
Script to execute Task T010: Run the Linear Probe Adapter Pipeline.
"""
import os
import sys
import logging
import torch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code', 'src'))

from controller_adapter import run_adapter_pipeline, LinearProbe, ValidationFailedError
from config import DATA_PROCESSED_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting T010: Controller Adapter Pipeline")
    try:
        # Ensure output directory exists
        os.makedirs(DATA_PROCESSED_PATH, exist_ok=True)
        
        # Run the pipeline
        # Note: This will attempt to stream real data from RoboDojo/RoboDojo-v1
        # and raise an error if validation fails.
        probe, metrics = run_adapter_pipeline(
            input_dim=512,
            output_dim=7,
            lr=1e-3,
            epochs=5,
            batch_size=2,
            val_threshold=0.6,
            device='cpu' # Force CPU for CI/CD compatibility if needed
        )
        
        logger.info(f"Pipeline completed successfully.")
        logger.info(f"Metrics: {metrics}")
        
    except ValidationFailedError as e:
        logger.error(f"Validation Failed: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
