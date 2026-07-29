"""
Main pipeline orchestrator for llmXive: Measuring Epistemic Resilience of LLMs Under Misleading Medical Context.
This script orchestrates the full pipeline from ingestion to final result generation.
"""
import logging
import sys
from pathlib import Path

from config import get_config
from validation import start_pipeline_timer, stop_pipeline_timer, check_pipeline_limit
from ingestion import run_ingestion_pipeline
from static_ground_truth import run_static_ground_truth_pipeline
from features import run_feature_extraction_pipeline
from feature_save import run_feature_save_pipeline
from labeling import run_semantic_scoring_pipeline
from modeling import run_modeling_pipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    """Execute the full research pipeline."""
    config = get_config()
    logger.info("Starting llmXive Epistemic Resilience Pipeline")

    # Start timing the pipeline
    start_pipeline_timer()

    try:
        # Step 1: Ingestion (T013) - Download MedMisBench and save subset
        logger.info("Phase 1: Data Ingestion")
        run_ingestion_pipeline()

        # Check time limit
        if not check_pipeline_limit():
            raise RuntimeError("Pipeline execution time limit exceeded during ingestion.")

        # Step 2: Static Ground Truth (T020/T021) - Fetch PubMed facts
        logger.info("Phase 2: Dynamic Ground Truth Retrieval")
        run_static_ground_truth_pipeline()

        if not check_pipeline_limit():
            raise RuntimeError("Pipeline execution time limit exceeded during ground truth retrieval.")

        # Step 3: Feature Extraction (T014/T015) - Extract linguistic features
        logger.info("Phase 3: Linguistic Feature Extraction")
        run_feature_extraction_pipeline()

        if not check_pipeline_limit():
            raise RuntimeError("Pipeline execution time limit exceeded during feature extraction.")

        # Step 4: Save Features (T016) - Save final feature-rich dataset
        logger.info("Phase 4: Saving Feature Dataset")
        run_feature_save_pipeline()

        if not check_pipeline_limit():
            raise RuntimeError("Pipeline execution time limit exceeded during feature saving.")

        # Step 5: Labeling (T022-T025) - Semantic scoring and adherence labeling
        logger.info("Phase 5: Model Inference and Adherence Labeling")
        run_semantic_scoring_pipeline()

        if not check_pipeline_limit():
            raise RuntimeError("Pipeline execution time limit exceeded during labeling.")

        # Step 6: Modeling (T029-T035) - Statistical analysis
        logger.info("Phase 6: Statistical Modeling and Sensitivity Analysis")
        run_modeling_pipeline()

        if not check_pipeline_limit():
            raise RuntimeError("Pipeline execution time limit exceeded during modeling.")

        logger.info("Pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        raise
    finally:
        stop_pipeline_timer()

if __name__ == "__main__":
    main()
