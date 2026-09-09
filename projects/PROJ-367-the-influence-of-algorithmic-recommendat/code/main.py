"""
Main entry point for the Algorithmic Recommendations Analysis Pipeline.
Orchestrates ingestion, metric calculation, modeling, robustness checks, and reporting.
Includes runtime instrumentation for SC-005 (6-hour limit verification).
"""
import os
import sys
import logging
import time
import json
from pathlib import Path
from datetime import datetime

# Project-relative imports based on provided API surface
from config import ProjectConfig, setup_logging
from ingestion import load_project_data, ingest_and_clean
from metrics import calculate_batch_diversity_scores
from modeling import run_ps_analysis, RegressionResult
from robustness import run_robustness_suite
from reporting import generate_final_report
from audit_report import audit_and_sanitize_report

# Global timing dictionary to track stage durations
_stage_timings = {}
_total_start_time = None

def _start_stage(stage_name: str):
    """Start timing a specific pipeline stage."""
    _stage_timings[stage_name] = {
        'start': time.time(),
        'end': None,
        'duration_sec': None
    }

def _end_stage(stage_name: str):
    """End timing a specific pipeline stage and calculate duration."""
    if stage_name not in _stage_timings:
        logging.warning(f"Attempted to end stage {stage_name} that was not started.")
        return
    _stage_timings[stage_name]['end'] = time.time()
    _stage_timings[stage_name]['duration_sec'] = (
        _stage_timings[stage_name]['end'] - _stage_timings[stage_name]['start']
    )
    logging.info(f"Stage '{stage_name}' completed in {_stage_timings[stage_name]['duration_sec']:.2f} seconds.")

def run_verification_test():
    """
    Runs a quick verification test with hardcoded data to ensure entropy calculation is correct.
    Uses the example from T015: {'categories': ['Math', 'Math', 'Science']}
    Expected entropy: - (2/3 * log2(2/3) + 1/3 * log2(1/3)) ≈ 0.918
    """
    logging.info("Running verification test...")
    from metrics import shannon_entropy
    
    # Hardcoded test case
    test_categories = ['Math', 'Math', 'Science']
    expected_entropy = 0.9182958340544896 # - (2/3 * log2(2/3) + 1/3 * log2(1/3))
    
    calculated = shannon_entropy(test_categories)
    
    if abs(calculated - expected_entropy) < 0.001:
        logging.info(f"Verification passed: Calculated {calculated:.6f} matches expected {expected_entropy:.6f}")
        return True
    else:
        logging.error(f"Verification failed: Calculated {calculated:.6f} does not match expected {expected_entropy:.6f}")
        return False

def main():
    """
    Orchestrates the full pipeline with runtime instrumentation.
    """
    global _total_start_time
    _total_start_time = time.time()
    
    # Setup logging with timestamp
    log_dir = Path("projects/PROJ-367-the-influence-of-algorithmic-recommendat/docs/reports")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"pipeline_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("PipelineMain")
    logger.info("Pipeline execution started.")
    
    try:
        # 1. Configuration
        _start_stage("configuration")
        config = ProjectConfig()
        logger.info(f"Configuration loaded. Root: {config.root_dir}")
        _end_stage("configuration")

        # 2. Data Ingestion
        _start_stage("ingestion")
        raw_data = load_project_data(config.data_raw_dir / "synthetic_enrollments.csv")
        clean_data = ingest_and_clean(raw_data, config)
        logger.info(f"Ingestion complete. Rows after cleaning: {len(clean_data)}")
        _end_stage("ingestion")

        # 3. Metric Calculation
        _start_stage("metrics")
        diversity_results = calculate_batch_diversity_scores(clean_data, config.similarity_threshold)
        logger.info(f"Metrics calculated for {len(diversity_results)} sessions.")
        _end_stage("metrics")

        # 4. Modeling (PSW + GLS Fallback)
        _start_stage("modeling")
        model_results = run_ps_analysis(diversity_results, config)
        logger.info(f"Modeling complete. Method: {model_results.method}")
        _end_stage("modeling")

        # 5. Robustness (Permutation + Sensitivity)
        _start_stage("robustness")
        robustness_results = run_robustness_suite(model_results, config)
        logger.info(f"Robustness suite complete. Permutation p-value: {robustness_results.permutation_p_value:.4f}")
        _end_stage("robustness")

        # 6. Reporting & Audit
        _start_stage("reporting")
        # Generate the final report including runtime stats
        runtime_stats = {
            'total_runtime_seconds': time.time() - _total_start_time,
            'total_runtime_minutes': (time.time() - _total_start_time) / 60,
            'stage_timings': _stage_timings
        }
        
        report_path = generate_final_report(
            model_results, 
            robustness_results, 
            runtime_stats,
            output_path=config.report_dir / "final_analysis.md"
        )
        
        # Audit the report for associational framing
        audit_and_sanitize_report(report_path)
        _end_stage("reporting")

        logger.info("Pipeline execution completed successfully.")
        logger.info(f"Total Runtime: {runtime_stats['total_runtime_minutes']:.2f} minutes")
        
        # Verify SC-005
        if runtime_stats['total_runtime_minutes'] > 360: # 6 hours
            logger.warning(f"Runtime exceeded 6-hour limit: {runtime_stats['total_runtime_minutes']:.2f} min")
        else:
            logger.info(f"Runtime within 6-hour limit: {runtime_stats['total_runtime_minutes']:.2f} min")

        return 0

    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())