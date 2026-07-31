import argparse
import logging
import sys
from pathlib import Path

from code.config import (
    CONFIG,
    get_processed_path,
    get_raw_path,
)
from code.services.data_ingestion import run_data_ingestion_pipeline
from code.services.anxiety_scoring import run_full_scoring_pipeline
from code.services.proxy_extractor import run_proxy_extraction_pipeline
from code.services.coverage_validation import run_coverage_validation
from code.analysis.statistical_test import run_statistical_analysis_pipeline
from code.viz.save_visualization import main as save_viz_main

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

def stage_01_data_ingestion():
    """Download and validate the raw dataset."""
    logger.info("Stage 01: Data Ingestion")
    run_data_ingestion_pipeline()
    logger.info("Stage 01: Complete")

def stage_02_preprocessing():
    """Filter non-English/gibberish text."""
    logger.info("Stage 02: Preprocessing")
    # This logic is integrated into anxiety_scoring in current impl, 
    # but kept as a stage for pipeline structure if separated later.
    # Currently, T014a logic is inside anxiety_scoring pipeline.
    logger.info("Stage 02: Complete (Integrated in Stage 03)")

def stage_03_anxiety_scoring():
    """Compute anxiety scores and filter by confidence."""
    logger.info("Stage 03: Anxiety Scoring")
    run_full_scoring_pipeline()
    logger.info("Stage 03: Complete")

def stage_04_proxy_extraction():
    """Extract control proxies from metadata."""
    logger.info("Stage 04: Proxy Extraction")
    run_proxy_extraction_pipeline()
    logger.info("Stage 04: Complete")

def stage_05_merge_and_validate():
    """
    Merge scoring results and proxy results on post_id.
    Confirm data is pre-filtered (from T016) and save final dataset.
    """
    logger.info("Stage 05: Merge and Validate")
    
    scoring_path = get_processed_path("scoring_results.csv")
    proxy_path = get_processed_path("proxy_results.csv")
    output_path = get_processed_path("final_analysis.csv")

    logger.info(f"Loading scoring results from {scoring_path}")
    df_scores = pd.read_csv(scoring_path)
    
    logger.info(f"Loading proxy results from {proxy_path}")
    df_proxies = pd.read_csv(proxy_path)

    # Verify pre-filtering: Check for nulls in key columns if any logic missed
    # T016 handles filtering, so we assume df_scores is clean, but we log counts.
    logger.info(f"Scoring rows before merge: {len(df_scores)}")
    logger.info(f"Proxy rows before merge: {len(df_proxies)}")

    # Merge on post_id. 
    # Note: scoring_results has 'text', 'anxiety_score', 'confidence_score'.
    # proxy_results has 'post_id', 'user_id', 'control_proxy', 'timestamp_regularity'.
    # We need to ensure 'post_id' exists in both.
    
    # Check if post_id exists in scoring results (it should from ingestion)
    if 'post_id' not in df_scores.columns:
        # Fallback: if the scoring pipeline didn't preserve post_id, we might need to handle it.
        # Based on T017 spec: "columns: text, anxiety_score, confidence_score". 
        # However, T013 downloads 'cardiffnlp/tweet_sentiment_extraction' which usually has 'tweet_id'.
        # We assume the ingestion/scoring pipeline preserves 'post_id' or 'tweet_id' as 'post_id'.
        # If not, this merge will fail, which is correct behavior for data integrity.
        logger.error("post_id column missing in scoring_results.csv. Cannot merge.")
        raise ValueError("Missing 'post_id' in scoring results.")

    if 'post_id' not in df_proxies.columns:
        logger.error("post_id column missing in proxy_results.csv. Cannot merge.")
        raise ValueError("Missing 'post_id' in proxy results.")

    df_merged = pd.merge(
        df_scores, 
        df_proxies, 
        on='post_id', 
        how='inner'
    )

    logger.info(f"Rows after merge: {len(df_merged)}")
    
    if len(df_merged) == 0:
        logger.warning("Merge resulted in 0 rows. Check key alignment.")

    # Save final dataset
    df_merged.to_csv(output_path, index=False)
    logger.info(f"Saved final merged dataset to {output_path}")
    logger.info("Stage 05: Complete")

def stage_06_statistical_analysis():
    """Run statistical tests on merged data."""
    logger.info("Stage 06: Statistical Analysis")
    run_statistical_analysis_pipeline()
    logger.info("Stage 06: Complete")

def stage_07_visualization():
    """Generate and save visualization."""
    logger.info("Stage 07: Visualization")
    save_viz_main()
    logger.info("Stage 07: Complete")

def run_pipeline():
    """Orchestrate the full pipeline."""
    logger.info("Starting full pipeline...")
    stage_01_data_ingestion()
    stage_02_preprocessing()
    stage_03_anxiety_scoring()
    stage_04_proxy_extraction()
    stage_05_merge_and_validate()
    stage_06_statistical_analysis()
    stage_07_visualization()
    logger.info("Pipeline complete.")

def main():
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument(
        "--stage",
        type=str,
        choices=[
            "ingestion", "preprocessing", "scoring", "proxy", 
            "merge", "analysis", "viz", "all"
        ],
        default="all",
        help="Which stage to run"
    )
    args = parser.parse_args()

    if args.stage == "ingestion":
        stage_01_data_ingestion()
    elif args.stage == "preprocessing":
        stage_02_preprocessing()
    elif args.stage == "scoring":
        stage_03_anxiety_scoring()
    elif args.stage == "proxy":
        stage_04_proxy_extraction()
    elif args.stage == "merge":
        stage_05_merge_and_validate()
    elif args.stage == "analysis":
        stage_06_statistical_analysis()
    elif args.stage == "viz":
        stage_07_visualization()
    elif args.stage == "all":
        run_pipeline()

if __name__ == "__main__":
    main()
