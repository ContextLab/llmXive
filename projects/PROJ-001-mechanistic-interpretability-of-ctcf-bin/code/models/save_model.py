"""
Save trained CTCF predictor model weights to disk.

This script loads the best model state dictionary produced by the training
pipeline and saves it to the designated output path:
`data/models/best_ctcf_predictor.pth`.

It ensures the output directory exists and logs the save operation.
"""
import os
import sys
import logging
import torch
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.predictor import CTCFPredictor, load_model
from models.train import save_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OUTPUT_DIR = PROJECT_ROOT / "data" / "models"
OUTPUT_FILE = OUTPUT_DIR / "best_ctcf_predictor.pth"
METRICS_FILE = PROJECT_ROOT / "data" / "models" / "training_metrics.json"

def ensure_output_dir():
    """Create the output directory if it does not exist."""
    if not OUTPUT_DIR.exists():
        logger.info(f"Creating output directory: {OUTPUT_DIR}")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def load_best_model_state() -> Dict[str, Any]:
    """
    Load the best model state from the training checkpoint.
    
    The training script (code/models/train.py) is expected to save the best
    model state to a specific location or update the metrics file with the
    path to the best checkpoint. For this implementation, we assume the
    training process leaves the best state in memory or a temporary location
    that we can access via the `load_model` helper if a path is provided,
    or we re-instantiate and load from the standard training checkpoint location.
    
    In the context of the pipeline, `train.py` typically saves the best model
    as `best_model.pth` in the output directory. We will look for that or
    attempt to load from the metrics reference if available.
    
    For robustness, we will attempt to load from the standard training checkpoint
    path if `load_model` supports it, or we assume the training script has
    already saved a `best_model.pth` in the output directory.
    """
    # Standard location where train.py saves the best model
    training_best_path = OUTPUT_DIR / "best_model.pth"
    
    if training_best_path.exists():
        logger.info(f"Loading best model state from: {training_best_path}")
        state_dict = torch.load(training_best_path, map_location='cpu')
        return state_dict
    else:
        # Fallback: Try to load from a generic checkpoint if it exists
        # This handles cases where the training script might have named it differently
        checkpoint_files = list(OUTPUT_DIR.glob("*.pth"))
        if checkpoint_files:
            # Sort by modification time, take the latest
            latest = max(checkpoint_files, key=os.path.getmtime)
            logger.warning(f"Using latest checkpoint {latest} as best model.")
            return torch.load(latest, map_location='cpu')
        
        raise FileNotFoundError(
            f"No trained model weights found in {OUTPUT_DIR}. "
            "Please run code/models/train.py first to generate the model."
        )

def save_model_weights(state_dict: Dict[str, Any]):
    """Save the model weights to the final output path."""
    logger.info(f"Saving model weights to: {OUTPUT_FILE}")
    torch.save(state_dict, OUTPUT_FILE)
    logger.info("Model weights saved successfully.")

def main():
    """Main entry point for saving the trained model."""
    logger.info("Starting model save process (T024).")
    
    try:
        # Ensure output directory exists
        ensure_output_dir()
        
        # Load the best model state
        state_dict = load_best_model_state()
        
        # Save to the designated T024 output path
        save_model_weights(state_dict)
        
        # Verify the file exists
        if OUTPUT_FILE.exists():
            file_size = OUTPUT_FILE.stat().st_size
            logger.info(f"Verification: {OUTPUT_FILE} exists (size: {file_size} bytes).")
            logger.info("T024 completed successfully.")
            return 0
        else:
            logger.error("Verification failed: Output file was not created.")
            return 1

    except FileNotFoundError as e:
        logger.error(f"Model file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during model save: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())