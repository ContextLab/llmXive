"""
Orchestration script for the Dataset Imbalance Assessment Pipeline.

Executes the full workflow:
1. Ingestion (fetch raw data)
2. Descriptors (compute Magpie features)
3. Imbalance Calculation (Target & Compositional scores)
4. Baseline Training (RF & GB models on skewed data)
5. Evaluation (generate baseline report)
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to ensure imports work regardless of CWD
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "results" / "pipeline_run.log")
    ]
)
logger = logging.getLogger("main")

def run_pipeline():
    """Execute the full pipeline steps in order."""
    logger.info("Starting Dataset Imbalance Assessment Pipeline...")
    
    # Ensure output directories exist
    (DATA_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR).mkdir(parents=True, exist_ok=True)

    # Step 1: Ingestion
    logger.info("Step 1: Running Ingestion...")
    try:
        from ingestion import main as ingestion_main
        # Run ingestion to populate data/raw/
        ingestion_main()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

    # Step 2: Descriptors
    logger.info("Step 2: Computing Descriptors...")
    try:
        from descriptors import main as descriptors_main
        # Run descriptors to populate data/processed/
        descriptors_main()
    except Exception as e:
        logger.error(f"Descriptor computation failed: {e}")
        raise

    # Step 3: Imbalance Calculation
    logger.info("Step 3: Calculating Imbalance Scores...")
    try:
        from imbalance import main as imbalance_main
        # Calculate Target and Compositional imbalance scores
        imbalance_main()
    except Exception as e:
        logger.error(f"Imbalance calculation failed: {e}")
        raise

    # Step 4: Baseline Training
    logger.info("Step 4: Training Baseline Models...")
    try:
        from training import main as training_main
        # Train RF and GB models on skewed data
        training_main()
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise

    # Step 5: Evaluation
    logger.info("Step 5: Generating Evaluation Report...")
    try:
        from evaluation import main as evaluation_main
        # Generate baseline_report.csv
        evaluation_main()
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    run_pipeline()