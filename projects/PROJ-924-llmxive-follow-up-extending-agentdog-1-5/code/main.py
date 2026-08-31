import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from config import set_seed, get_config, get_path, ensure_directories, get_batch_size, RANDOM_SEED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_data_validation():
    """Run data validation steps."""
    logger.info("Running data validation...")
    # Import and run data loading
    from data_loader import fetch_atbench, map_atbench_labels
    
    # Fetch ATBench
    atbench_path = get_path("raw_data") / "ATBench_raw.parquet"
    if not atbench_path.exists():
        df = fetch_atbench(output_path=atbench_path)
        logger.info(f"Fetched ATBench with {len(df)} records")
    
    # Map labels
    mapped_path = get_path("processed") / "ATBench_mapped.csv"
    if not mapped_path.exists():
        map_atbench_labels(atbench_path, mapped_path)
        logger.info(f"Mapped ATBench labels to {mapped_path}")

def run_taxonomy_building():
    """Run taxonomy building steps."""
    logger.info("Running taxonomy building...")
    from taxonomy_builder import load_taxonomy, build_centroids, save_centroids
    
    # Load taxonomy
    taxonomy = load_taxonomy()
    
    # Build centroids
    centroids = build_centroids(taxonomy)
    
    # Save centroids
    output_path = get_path("processed") / "taxonomy_centroids.json"
    save_centroids(centroids, output_path)
    logger.info(f"Saved centroids to {output_path}")

def run_drift_scoring():
    """Run drift scoring pipeline."""
    logger.info("Running drift scoring...")
    from drift_scoring import load_centroids, batch_process_logs, export_results
    from sentence_transformers import SentenceTransformer
    
    # Load centroids
    centroids_path = get_path("processed") / "taxonomy_centroids.json"
    centroids = load_centroids(centroids_path)
    
    # Load model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    # Load logs
    logs_path = get_path("raw_data") / "ATBench_raw.parquet"
    import pandas as pd
    logs = pd.read_parquet(logs_path).to_dict('records')
    
    # Process logs
    results = batch_process_logs(logs, model, centroids)
    
    # Export results
    output_path = get_path("processed") / "drift_scores.csv"
    export_results(results, output_path)
    logger.info(f"Saved drift scores to {output_path}")

def main():
    """Main entry point for the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the full drift detection pipeline")
    parser.add_argument("--validate-only", action="store_true", help="Run only validation steps")
    parser.add_argument("--skip-taxonomy", action="store_true", help="Skip taxonomy building")
    parser.add_argument("--skip-dataset-fetch", action="store_true", help="Skip dataset fetching")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(RANDOM_SEED)
    
    # Ensure directories
    ensure_directories([
        str(get_path("raw_data")),
        str(get_path("processed")),
        str(get_path("test"))
    ])
    
    if not args.validate_only:
        # Run data validation
        if not args.skip_dataset_fetch:
            run_data_validation()
        
        # Run taxonomy building
        if not args.skip_taxonomy:
            run_taxonomy_building()
        
        # Run drift scoring
        run_drift_scoring()
    
    # Run validation
    from validation import run_us01_validation, save_validation_results, check_acceptance_criteria
    
    results = run_us01_validation()
    meets_criteria = check_acceptance_criteria(results)
    results["meets_criteria"] = meets_criteria
    
    output_path = get_path("processed") / "us01_final_stats.json"
    save_validation_results(results, output_path)
    
    logger.info(f"Validation results saved to {output_path}")
    
    if not meets_criteria:
        logger.error("Validation FAILED: Acceptance criteria not met.")
        sys.exit(1)
    else:
        logger.info("Validation PASSED: Acceptance criteria met.")

if __name__ == "__main__":
    main()