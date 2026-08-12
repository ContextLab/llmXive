import os
import sys
import json
import pickle
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_paths
from utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

def save_artifacts(rf_model, gb_model, metrics):
    paths = load_paths()
    with open(paths["evaluation"] / "model_rf.pkl", "wb") as f:
        pickle.dump(rf_model, f)
    with open(paths["evaluation"] / "model_gb.pkl", "wb") as f:
        pickle.dump(gb_model, f)
    with open(paths["evaluation"] / "model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

def main():
    setup_logging()
    logger.info("Model saving module ready.")

if __name__ == "__main__":
    main()
