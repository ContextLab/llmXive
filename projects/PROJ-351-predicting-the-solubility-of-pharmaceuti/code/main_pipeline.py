"""
Main Pipeline Execution Script for T045: End-to-End Pipeline Verification.

This script orchestrates the full research workflow:
1. Download ESOL Dataset (T004)
2. Preprocess & Clean (T005)
3. Graph Tensorization (T005b)
4. Stratified Splitting (T006)
5. Random Forest Nested CV (T016)
6. GNN Nested CV (T021)
7. Aggregate Predictions (T033)
8. Statistical Testing (T028)
9. Interpretability & Viz (T029, T030)
10. Metrics Aggregation (T032)
11. Report Generation (T031, T034)
12. Ceiling Effect Check (T034)

It validates SC-003 (Computational Feasibility) by logging total runtime.
"""

import os
import sys
import time
import logging
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.seeds import ensure_seeded, get_seed
from data.download_esol import main as download_main
from data.preprocess import main as preprocess_main
from data.graph_tensorizer import main as tensorizer_main
from data.split import main as split_main
from models.baseline_rf import main as rf_main
from training.train_baseline_cv import main as rf_cv_main
from models.gnn_mpnn import main as gnn_model_main
from training.train_gnn_cv import main as gnn_cv_main
from evaluation.aggregate_predictions import main as aggregate_main
from evaluation.statistical_test import main as stats_main
from evaluation.interpretability import main as interpret_main
from evaluation.metrics import main as eval_metrics_main
from evaluation.write_metrics import main as write_metrics_main
from evaluation.report_generator import main as report_main
from evaluation.ceiling_effect import main as ceiling_main

# Setup Logging for Pipeline
def setup_pipeline_logger():
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"pipeline_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def run_stage(name, func, *args, **kwargs):
    logger = logging.getLogger(__name__)
    logger.info(f"--- STARTING STAGE: {name} ---")
    start = time.time()
    try:
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"--- COMPLETED STAGE: {name} in {elapsed:.2f}s ---")
        return result
    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"--- FAILED STAGE: {name} after {elapsed:.2f}s ---")
        logger.error(f"Error: {str(e)}")
        raise

def main():
    logger = setup_pipeline_logger()
    logger.info("Starting End-to-End Pipeline Verification (T045)")
    start_total = time.time()

    try:
        # 0. Environment Setup
        logger.info("Setting random seeds...")
        ensure_seeded(get_seed())

        # 1. Download Data
        # The download script handles fetching from S3 or HF mirror
        run_stage("Download ESOL", download_main)

        # 2. Preprocess & Clean
        # Loads raw CSV, validates SMILES, saves cleaned Mol objects
        run_stage("Preprocess & Clean", preprocess_main)

        # 3. Graph Tensorization
        # Converts cleaned Mol objects to PyG tensors
        run_stage("Graph Tensorization", tensorizer_main)

        # 4. Split Data
        # Stratified 5-fold split based on logS
        run_stage("Stratified Split", split_main)

        # 5. Random Forest Baseline (Nested CV)
        # T016: Nested CV for RF
        run_stage("Random Forest Nested CV", rf_cv_main)

        # 6. GNN Model (Nested CV)
        # T021: Nested CV for GNN
        run_stage("GNN Nested CV", gnn_cv_main)

        # 7. Aggregate Predictions
        # T033: Combine per-fold predictions
        run_stage("Aggregate Predictions", aggregate_main)

        # 8. Statistical Testing
        # T028: Nadeau's t-test, Power, Cohens D
        run_stage("Statistical Analysis", stats_main)

        # 9. Interpretability & Visualization
        # T029/T030: Generate heatmaps and rankings
        run_stage("Interpretability & Viz", interpret_main)

        # 10. Evaluate Metrics (GNN specific if needed, though T021/T016 save fold metrics)
        # T023/T024: Ensure final metrics are saved
        run_stage("Evaluation Metrics", eval_metrics_main)

        # 11. Write Aggregated Metrics
        # T032: Write to results/metrics.json
        run_stage("Write Aggregated Metrics", write_metrics_main)

        # 12. Ceiling Effect Check
        # T034: Check if Baseline R2 > 0.9
        run_stage("Ceiling Effect Check", ceiling_main)

        # 13. Final Report Generation
        # T031: Compile final report
        run_stage("Final Report Generation", report_main)

        end_total = time.time()
        total_elapsed = end_total - start_total
        
        logger.info("=" * 50)
        logger.info(f"PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"Total Runtime: {total_elapsed:.2f} seconds ({total_elapsed/3600:.2f} hours)")
        logger.info(f"Constraint Check (SC-003): {'PASS' if total_elapsed < 21600 else 'FAIL'} (Limit: 6 hours)")
        logger.info("=" * 50)

        # Write a summary file for T045 verification
        summary_path = PROJECT_ROOT / "results" / "pipeline_verification.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(summary_path, 'w') as f:
            json.dump({
                "status": "success",
                "total_runtime_seconds": total_elapsed,
                "within_6_hour_limit": total_elapsed < 21600,
                "timestamp": datetime.now().isoformat(),
                "stages_completed": [
                    "Download", "Preprocess", "Tensorize", "Split",
                    "RF_CV", "GNN_CV", "Aggregate", "Stats",
                    "Interpret", "Metrics", "Ceiling", "Report"
                ]
            }, f, indent=2)

    except Exception as e:
        logger.critical(f"PIPELINE FAILED: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()