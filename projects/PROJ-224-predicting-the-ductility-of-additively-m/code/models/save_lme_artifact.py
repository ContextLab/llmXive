"""
Save LME artifact module.
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_lme_artifact():
    """Save LME results artifact."""
    logger.info("Saving LME artifact...")
    input_path = Path(__file__).parent.parent.parent / "artifacts" / "lme_results.json"
    output_path = Path(__file__).parent.parent.parent / "artifacts" / "MixedEffectsResult.json"
    
    if not input_path.exists():
        logger.error("LME results not found.")
        sys.exit(1)
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Add metadata
    artifact = {
        "artifact_type": "MixedEffectsResult",
        "version": "1.0",
        "data": data
    }
    
    with open(output_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    
    logger.info(f"LME artifact saved to {output_path}")
    return artifact

def main():
    """Main entry point."""
    logger.info("Starting Save LME Artifact...")
    save_lme_artifact()
    logger.info("Save LME Artifact stage completed.")

if __name__ == "__main__":
    main()
