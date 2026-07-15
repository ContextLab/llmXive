"""
Save Predictive Artifact Module.
"""
import os
import sys
import logging
import json
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_training_results():
    """Load training results."""
    path = Path(__file__).parent.parent.parent / "artifacts" / "PredictiveModelArtifact.json"
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return None

def save_predictive_artifact():
    """Save predictive artifact."""
    logger.info("Saving predictive artifact...")
    data = load_training_results()
    if not data:
        logger.error("No training results found.")
        sys.exit(1)
    
    output_path = Path(__file__).parent.parent.parent / "artifacts" / "final_predictive_artifact.json"
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Predictive artifact saved to {output_path}")

def main():
    """Main entry point."""
    logger.info("Starting Save Predictive Artifact...")
    save_predictive_artifact()
    logger.info("Save Predictive Artifact stage completed.")

if __name__ == "__main__":
    main()
