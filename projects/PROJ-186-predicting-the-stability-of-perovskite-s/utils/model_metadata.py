import os
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from utils.logging_config import get_logger, log_pipeline_event

logger = get_logger(__name__)

RESULTS_DIR = Path("results")
MODEL_FILE = RESULTS_DIR / "model.pkl"
METADATA_FILE = RESULTS_DIR / "model_metadata.json"

def save_model_metadata(model, metrics: Dict[str, Any], cv_results: Dict[str, Any]):
    """
    Save metadata about the trained model including hyperparameters, 
    training metrics, and DFT functional information.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "model_type": "RandomForestRegressor",
        "hyperparameters": model.get_params(),
        "training_metrics": metrics,
        "cv_results_summary": {
            "best_params": cv_results.get("best_params", {}),
            "best_cv_rmse": cv_results.get("best_cv_rmse", 0.0)
        },
        "dft_functional": "PBE",  # Explicitly stated as per SC-001
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Model metadata saved to {METADATA_FILE}")
    return metadata

def load_model_metadata() -> Optional[Dict[str, Any]]:
    """Load model metadata from disk."""
    if not METADATA_FILE.exists():
        return None
    
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def verify_dft_functional() -> bool:
    """Verify that the model metadata explicitly states the DFT functional."""
    metadata = load_model_metadata()
    if not metadata:
        logger.error("Model metadata not found.")
        return False
    
    functional = metadata.get("dft_functional")
    if functional != "PBE":
        logger.warning(f"Expected DFT functional 'PBE', found '{functional}'")
        return False
    
    logger.info("DFT functional verified: PBE")
    return True

def embed_metadata_in_model(model, metadata: Dict[str, Any]):
    """Embed metadata directly into the model object (optional)."""
    model._metadata = metadata
    logger.info("Metadata embedded in model object")

def extract_metadata_from_model(model) -> Optional[Dict[str, Any]]:
    """Extract metadata from the model object if it exists."""
    return getattr(model, '_metadata', None)

def main():
    """Main entry point for metadata verification."""
    log_pipeline_event("Verifying model metadata")
    
    if not MODEL_FILE.exists():
        logger.error(f"Model file not found: {MODEL_FILE}")
        return False
    
    if not verify_dft_functional():
        logger.error("DFT functional verification failed")
        return False
    
    logger.info("Metadata verification passed")
    return True

if __name__ == "__main__":
    main()