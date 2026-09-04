"""
Script to execute Task T010: Controller Adapter Training Pipeline.

This script runs the full adapter training process as specified:
1. Split tasks into training and validation sets
2. Train the probe on training tasks
3. Validate on hold-out tasks
4. Discard split weights
5. Retrain on ALL tasks
6. Save final weights to data/processed/adapter_weights.pt
"""
import os
import sys
import logging
import torch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from controller_adapter import run_adapter_pipeline, LinearProbe
from config import DATA_PROCESSED_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for T010 execution."""
    logger.info("Starting Task T010: Controller Adapter Training Pipeline")
    
    # Ensure output directory exists
    os.makedirs(DATA_PROCESSED_PATH, exist_ok=True)
    
    try:
        # Run the full adapter pipeline
        adapter, metrics = run_adapter_pipeline(
            num_epochs=50,
            learning_rate=1e-3,
            batch_size=32
        )
        
        # Verify output file exists
        output_path = os.path.join(DATA_PROCESSED_PATH, "adapter_weights.pt")
        if os.path.exists(output_path):
            logger.info(f"Successfully created: {output_path}")
            file_size = os.path.getsize(output_path)
            logger.info(f"File size: {file_size} bytes")
            
            # Verify weights can be loaded
            checkpoint = torch.load(output_path, map_location='cpu', weights_only=True)
            logger.info(f"Checkpoint keys: {list(checkpoint.keys())}")
            logger.info(f"Model state dict size: {len(checkpoint['model_state_dict'])} layers")
        else:
            raise FileNotFoundError(f"Output file not created at {output_path}")
        
        logger.info("Task T010 completed successfully")
        
    except Exception as e:
        logger.error(f"Task T010 failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
