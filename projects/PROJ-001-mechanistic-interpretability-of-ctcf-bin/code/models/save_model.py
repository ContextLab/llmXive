"""
Model Saving Module for CTCF Predictor

This module handles the persistence of trained model weights to disk.
It ensures the output directory exists, loads the best model state
from the training process, and saves the weights in PyTorch format.
"""

import os
import sys
import logging
import torch
from pathlib import Path
from typing import Dict, Any, Optional

# Project root path resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_MODELS_DIR = PROJECT_ROOT / "data" / "models"

logger = logging.getLogger(__name__)

def ensure_output_dir(output_path: Path) -> None:
    """
    Ensures the directory containing the output file exists.
    
    Args:
        output_path: The full path to the file to be saved.
    """
    output_dir = output_path.parent
    if not output_dir.exists():
        logger.info(f"Creating output directory: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
    elif not output_dir.is_dir():
        raise NotADirectoryError(f"Path exists but is not a directory: {output_dir}")

def load_best_model_state(
    model: Any, 
    metrics: Dict[str, float], 
    best_metric_name: str = "val_auc"
) -> Dict[str, Any]:
    """
    Retrieves the state dictionary of the best model based on metrics.
    
    In a real training loop (T021), the model state is typically saved
    incrementally. This function assumes the 'model' passed is the current
    best candidate or retrieves the state if the training loop stored it
    in the metrics dictionary (e.g., 'best_model_state').
    
    Args:
        model: The PyTorch model instance (CTCFPredictor).
        metrics: Dictionary containing training metrics.
        best_metric_name: The key in metrics to track for "bestness".
        
    Returns:
        The state_dict of the best model.
    """
    # If the training loop stored the best state in metrics, use it.
    # This is a common pattern to avoid loading a file during the save step.
    if "best_model_state" in metrics:
        logger.info("Loading best model state from metrics dictionary.")
        return metrics["best_model_state"]
    
    # Fallback: If the model has been updated to the best state already,
    # simply return its state_dict.
    logger.info("Returning current model state (assuming it is the best).")
    return model.state_dict()

def save_model_weights(
    model: Any,
    metrics: Dict[str, float],
    output_path: Optional[Path] = None,
    best_metric_name: str = "val_auc"
) -> Path:
    """
    Saves the trained model weights to the specified path.
    
    Args:
        model: The PyTorch model instance.
        metrics: Dictionary containing training metrics (e.g., AUC, loss).
        output_path: Optional path for the .pth file. Defaults to 
                     data/models/best_ctcf_predictor.pth.
        best_metric_name: Key in metrics used to identify the best model state.
        
    Returns:
        The Path where the model was saved.
    """
    if output_path is None:
        output_path = DATA_MODELS_DIR / "best_ctcf_predictor.pth"
    
    ensure_output_dir(output_path)
    
    # Extract the state dictionary
    state_dict = load_best_model_state(model, metrics, best_metric_name)
    
    # Save the dictionary
    logger.info(f"Saving model weights to {output_path}")
    torch.save({
        "model_state_dict": state_dict,
        "metrics": metrics,
        "best_metric_name": best_metric_name
    }, str(output_path))
    
    logger.info(f"Model saved successfully to {output_path}")
    return output_path

def main():
    """
    Entry point for the save_model script.
    This is typically called from code/models/train.py after training completes.
    For standalone testing, it expects a mock model or arguments.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check if called directly for a dry run or specific test
    # In the pipeline, this function is imported and called by train.py
    if __name__ == "__main__":
        # Example usage if run directly (requires a model instance)
        # This block is primarily for documentation/testing the API
        logger.info("save_model module loaded. Call save_model_weights() from train.py.")
        return

if __name__ == "__main__":
    main()
