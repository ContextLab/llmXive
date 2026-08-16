"""
Main entry point for the llmXive research pipeline.
Orchestrates the full execution flow as per the quickstart run-book.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from data_loader import run_validation_pipeline, load_injected_dataset
from clustering import run_clustering_pipeline
from ranker import run_baseline_active_ranker, generate_unique_subset
from metrics import aggregate_flagged_pairs_from_log
from run_pipeline import run_single_seed_experiment
from logging_config import init_logging, get_comparison_log_path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Runner")
    parser.add_argument("--dataset", type=str, default="scifact", help="Dataset to use")
    parser.add_argument("--redundancy", type=float, default=0.4, help="Redundancy level")
    parser.add_argument("--seeds", type=int, default=30, help="Number of seeds for statistical testing")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    
    args = parser.parse_args()
    
    logger.info(f"Starting llmXive pipeline for {args.dataset}")
    logger.info(f"Parameters: redundancy={args.redundancy}, seeds={args.seeds}")
    
    # Ensure output directories exist
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("data/results", exist_ok=True)
    
    # Step 1: T012 - Synthetic Redundancy Injection
    logger.info("Step 1: Injecting synthetic redundancy (T012)...")
    injected_path = os.path.join(args.output_dir, "injected_datasets.json")
    
    try:
        result = run_validation_pipeline(
            dataset_name=args.dataset,
            output_path=injected_path,
            synonym_prob=args.redundancy,
            shuffle_window=2,
            target_clusters=20,
            seed=42
        )
        logger.info(f"Injected dataset written to {injected_path}")
    except Exception as e:
        logger.error(f"Failed to inject redundancy: {e}")
        sys.exit(1)
    
    # Step 2: T020 - MinHash-LSH Clustering
    logger.info("Step 2: Running clustering (T020)...")
    clusters_path = os.path.join(args.output_dir, "clusters.json")
    try:
        run_clustering_pipeline(
            input_path=injected_path,
            output_path=clusters_path,
            jaccard_threshold=0.95
        )
        logger.info(f"Clusters written to {clusters_path}")
    except Exception as e:
        logger.error(f"Failed to run clustering: {e}")
        sys.exit(1)
    
    # Step 3: Generate Unique Subset (T014 prerequisite)
    logger.info("Step 3: Generating unique subset...")
    unique_path = os.path.join(args.output_dir, "unique_subset.json")
    try:
        # This calls the ranker module to generate unique subset
        generate_unique_subset(
            injected_path=injected_path,
            clusters_path=clusters_path,
            output_path=unique_path
        )
        logger.info(f"Unique subset written to {unique_path}")
    except Exception as e:
        logger.error(f"Failed to generate unique subset: {e}")
        sys.exit(1)
    
    # Step 4: Run Baseline Active Ranker (T014)
    logger.info("Step 4: Running baseline active ranker (T014)...")
    try:
        run_baseline_active_ranker(
            unique_path=unique_path,
            injected_path=injected_path,
            output_log=get_comparison_log_path()
        )
        logger.info("Baseline ranker completed")
    except Exception as e:
        logger.error(f"Failed to run baseline ranker: {e}")
        sys.exit(1)
    
    # Step 5: Multi-seed execution (T027)
    logger.info(f"Step 5: Running multi-seed execution ({args.seeds} seeds)...")
    try:
        for seed in range(args.seeds):
            logger.info(f"Running seed {seed + 1}/{args.seeds}")
            run_single_seed_experiment(
                dataset=args.dataset,
                seed=seed,
                redundancy=args.redundancy
            )
        logger.info("Multi-seed execution completed")
    except Exception as e:
        logger.error(f"Multi-seed execution failed: {e}")
        sys.exit(1)
    
    logger.info("Pipeline completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
