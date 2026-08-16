import os
import sys
import argparse
from pathlib import Path

from config import load_paths
from utils.logging import setup_logging, get_logger

logger = get_logger(__name__)

def main() -> None:
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Materials Science Pipeline")
    parser.add_argument("--config", type=str, default=None, help="Config file path")
    args = parser.parse_args()
    
    paths = load_paths()
    setup_logging(paths["data_logs"] / "pipeline.log")
    
    logger.info("Starting pipeline")
    
    # Execute phases in order
    # Phase 1: Ingest
    logger.info("Phase 1: Ingest")
    from ingest import main as ingest_main
    ingest_main()
    
    # Phase 2: Descriptors
    logger.info("Phase 2: Descriptors")
    from descriptors import main as descriptors_main
    descriptors_main()
    
    # Phase 3: Train
    logger.info("Phase 3: Train")
    from train import main as train_main
    train_main()
    
    # Phase 4: Evaluate
    logger.info("Phase 4: Evaluate")
    from evaluate import main as evaluate_main
    evaluate_main()
    
    # Phase 5: Importance
    logger.info("Phase 5: Importance")
    from importance import main as importance_main
    importance_main()
    
    # Phase 6: Plots
    logger.info("Phase 6: Plots")
    from plots import main as plots_main
    plots_main()
    
    logger.info("Pipeline complete")

if __name__ == "__main__":
    main()
