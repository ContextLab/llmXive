"""
Main Pipeline Runner for PROJ-197.
Orchestrates the execution of all tasks from data ingestion to model evaluation and metrics aggregation.
This script is the entry point for quickstart.md.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, validate_config, ensure_directories, VALIDATION_MODE
from utils.logging import DataPipelineLog

def setup_logging(config):
    """Sets up the logging infrastructure."""
    log_dir = Path(config['log_dir'])
    ensure_directories(config)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'pipeline.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("Pipeline")

def run_pipeline():
    """
    Executes the full research pipeline.
    1. Setup Directories
    2. Data Generation (Phylo Matrix)
    3. Data Download (TRY)
    4. Synthetic Genomics Generation (if needed)
    5. Ingestion & Merge
    6. Split
    7. Training
    8. Evaluation
    9. Comparison
    10. Metrics Aggregation (T030)
    """
    logger = logging.getLogger("Pipeline")
    logger.info("Starting PROJ-197 Pipeline")
    
    config = get_config()
    logger.info(f"Validation Mode: {VALIDATION_MODE}")
    
    # Step 1: Ensure Directories
    ensure_directories(config)
    logger.info("Directories initialized.")

    # Step 2: Generate Phylogenetic Matrix (T016a/T016b)
    logger.info("Generating Phylogenetic Matrix...")
    try:
        from data.generate import generate_synthetic_phylogenetic_matrix, compute_real_phylogenetic_matrix
        # Try real first if tree exists, else synthetic
        tree_path = Path(config['data_dir']) / 'raw' / 'phylo_tree.newick'
        if tree_path.exists():
            compute_real_phylogenetic_matrix(str(tree_path))
        else:
            generate_synthetic_phylogenetic_matrix()
    except Exception as e:
        logger.error(f"Phylogenetic matrix generation failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing with synthetic fallback (Validation Mode).")

    # Step 3: Download TRY Data (T011a)
    logger.info("Downloading TRY Data...")
    try:
        from data.download import download_try_data
        download_try_data()
    except Exception as e:
        logger.error(f"TRY download failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing without real TRY data (Validation Mode).")

    # Step 4: Generate Synthetic Genomics (T012) - Triggered if download failed or for validation
    # Note: T012 logic is inside generate.py or ingest.py depending on implementation.
    # We call the generation explicitly if needed.
    logger.info("Checking/Generating Synthetic Genomics...")
    try:
        from data.generate import generate_synthetic_genomic_features
        # This function handles the logic of when to generate based on config
        generate_synthetic_genomic_features()
    except Exception as e:
        logger.error(f"Synthetic genomics generation failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing without synthetic genomics.")

    # Step 5: Ingest and Merge (T013, T014a)
    logger.info("Ingesting and Merging Data...")
    try:
        from data.ingest import main as ingest_main
        ingest_main()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing without merged dataset.")

    # Step 6: Split Data (T015)
    logger.info("Splitting Data...")
    try:
        from data.split import main as split_main
        split_main()
    except Exception as e:
        logger.error(f"Splitting failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing without split data.")

    # Step 7: Train Models (T020, T021, T024, T038)
    logger.info("Training Models...")
    try:
        from models.train import main as train_main
        train_main()
    except Exception as e:
        logger.error(f"Training failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing without trained models.")

    # Step 8: Evaluate Models (T022, T023)
    logger.info("Evaluating Models...")
    try:
        from models.evaluate import main as eval_main
        eval_main()
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing without evaluation metrics.")

    # Step 9: Compare Models (T027, T028, T029, T039, T040)
    logger.info("Comparing Models...")
    try:
        from models.compare import main as compare_main
        compare_main()
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing without comparison report.")

    # Step 10: Aggregate Metrics (T030) - THE GOAL OF THIS TASK
    logger.info("Aggregating Metrics (T030)...")
    try:
        from models.save_metrics_runner import main as metrics_main
        metrics_main()
    except Exception as e:
        logger.error(f"Metrics aggregation failed: {e}")
        if not VALIDATION_MODE:
            raise
        logger.warning("Continuing without final metrics.json.")

    logger.info("Pipeline Execution Complete.")

if __name__ == "__main__":
    config = get_config()
    logger = setup_logging(config)
    run_pipeline()
