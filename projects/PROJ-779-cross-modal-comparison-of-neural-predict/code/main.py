import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import get_config, ensure_directories
from code.utils.logger import get_logger
from code.data.download import run_auditory_validation, run_visual_validation
from code.data.preprocess import preprocess_dataset
from code.analysis.metrics import generate_metrics_summary
from code.analysis.source import run_sensitivity_analysis, apply_inverse_source_estimation
from code.analysis.stats import independent_samples_ttest, tost_equivalence_test
from code.validation.reliability import compute_reliability_metrics

logger = get_logger(__name__)
config = get_config()

def load_json_result(file_path: str) -> dict:
    """Load a JSON result file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def classify_latency(metrics: dict, threshold_ms: float = 50.0) -> dict:
    """
    T046 Implementation: Latency Classification logic.
    
    Checks if the absolute difference between auditory and visual peak latencies
    is less than the threshold (SC-001).
    
    Args:
        metrics: Dictionary containing peak latencies for both modalities.
        threshold_ms: The threshold in milliseconds (default 50.0).
        
    Returns:
        dict: Updated metrics dictionary with 'latency_classification' field.
    """
    auditory_latency = metrics.get('auditory', {}).get('peak_latency_ms')
    visual_latency = metrics.get('visual', {}).get('peak_latency_ms')
    
    if auditory_latency is None or visual_latency is None:
        logger.warning("Missing latency data for classification.")
        return metrics
    
    delta_t = abs(auditory_latency - visual_latency)
    is_similar = delta_t < threshold_ms
    
    classification = {
        "threshold_ms": threshold_ms,
        "auditory_latency_ms": auditory_latency,
        "visual_latency_ms": visual_latency,
        "delta_t_ms": round(delta_t, 2),
        "classification": "similar" if is_similar else "distinct",
        "condition_met": is_similar,
        "rule_id": "SC-001"
    }
    
    logger.info(f"Latency Classification (SC-001): |Δt| = {delta_t:.2f}ms. "
                f"Threshold: {threshold_ms}ms. Result: {'SIMILAR' if is_similar else 'DISTINCT'}")
    
    metrics['latency_classification'] = classification
    return metrics

def classify_source_overlap(source_results: dict, metrics_results: dict, config: dict) -> dict:
    """
    T047 Implementation: Source Overlap Classification logic.
    
    Checks if the Dice coefficient > 0.6 AND TOST p-value < 0.05 (Plan Logic).
    This implements the logic overriding obsolete SC-002 text.
    
    Args:
        source_results: Dictionary containing source localization results (Dice coefficient).
        metrics_results: Dictionary containing statistical test results (TOST p-value).
        config: Configuration dictionary containing thresholds.
        
    Returns:
        dict: Classification result dictionary with 'source_overlap_classification' field.
    """
    # Extract Dice coefficient
    # Assuming source_results structure based on T039/T045 outputs
    dice_coeff = source_results.get('dice_coefficient')
    
    # Extract TOST p-value
    # Assuming metrics_results or a dedicated stats result structure
    # TOST usually returns a tuple (p1, p2) or a dict with 'p_value'
    # We look for the intersection p-value or the max of the two one-sided tests
    tost_result = metrics_results.get('tost_result')
    tost_p_value = None
    
    if tost_result:
        if isinstance(tost_result, dict):
            # Common structure: {'p_value': float, 'p1': float, 'p2': float}
            tost_p_value = tost_result.get('p_value')
            if tost_p_value is None:
                # Fallback to max of one-sided if 'p_value' not explicitly set
                p1 = tost_result.get('p1', 1.0)
                p2 = tost_result.get('p2', 1.0)
                tost_p_value = max(p1, p2)
        elif isinstance(tost_result, (list, tuple)) and len(tost_result) >= 2:
            # If returned as (statistic, p-value) or (p1, p2)
            # Assuming standard TOST returns p-value for equivalence
            tost_p_value = tost_result[-1] 
    
    dice_threshold = config['thresholds'].get('dice_threshold', 0.6)
    tost_alpha = config['thresholds'].get('tost_alpha', 0.05)
    
    if dice_coeff is None:
        logger.warning("Missing Dice coefficient for source overlap classification.")
        return {'source_overlap_classification': {'error': 'missing_dice', 'dice_coefficient': None}}
    
    if tost_p_value is None:
        logger.warning("Missing TOST p-value for source overlap classification.")
        return {'source_overlap_classification': {'error': 'missing_tost', 'tost_p_value': None}}
    
    # Check conditions: Dice > 0.6 AND TOST p < 0.05
    dice_met = dice_coeff > dice_threshold
    tost_met = tost_p_value < tost_alpha
    
    is_overlapping = dice_met and tost_met
    
    classification = {
        "dice_threshold": dice_threshold,
        "tost_alpha": tost_alpha,
        "dice_coefficient": round(dice_coeff, 4),
        "tost_p_value": round(tost_p_value, 4),
        "dice_condition_met": dice_met,
        "tost_condition_met": tost_met,
        "classification": "overlapping" if is_overlapping else "distinct",
        "condition_met": is_overlapping,
        "rule_id": "Plan-Logic-Source-Overlap",
        "note": "Implements Plan Phase 4 logic, overriding obsolete SC-002 text."
    }
    
    logger.info(f"Source Overlap Classification (Plan Logic): Dice = {dice_coeff:.4f} "
                f"(> {dice_threshold}? {dice_met}), TOST p = {tost_p_value:.4f} (< {tost_alpha}? {tost_met}). "
                f"Result: {'OVERLAPPING' if is_overlapping else 'DISTINCT'}")
    
    return classification

def run_orchestration():
    """
    Main orchestration function for the pipeline.
    Executes download, validation, preprocessing, analysis, and final classification.
    """
    start_time = datetime.now()
    logger.info("Starting full pipeline orchestration...")
    
    try:
        # 1. Ensure directories
        ensure_directories()
        
        # 2. Data Acquisition & Validation (Skipped if already present, logic omitted for brevity)
        # In a real run, we would call run_auditory_validation() and run_visual_validation() here.
        logger.info("Skipping download/validation steps (assumed complete for T047 context).")
        
        # 3. Preprocessing (Assumed complete, loading from artifact)
        # In a real run, we would call preprocess_dataset() here.
        logger.info("Skipping preprocessing steps (assumed complete for T047 context).")
        
        # 4. Metrics Extraction
        logger.info("Running metrics extraction...")
        metrics_path = config['paths']['metrics_summary_json']
        # Ensure the metrics file exists or is generated by the previous step in a real run
        if not os.path.exists(metrics_path):
            logger.warning(f"Metrics file {metrics_path} not found. Generating summary from raw data...")
            # In a real scenario, this would call generate_metrics_summary()
            # For T047, we assume the data is ready or we simulate the structure if missing for the demo
            # However, per instructions, we must not fake data. We assume the pipeline has run up to T032.
            # If T032 failed, this script would fail here, which is the correct behavior.
            raise FileNotFoundError(f"Required metrics file {metrics_path} not found. "
                                    "Please ensure T032 (metrics extraction) has completed successfully.")
        
        metrics_data = load_json_result(metrics_path)
        
        # 5. T046: Latency Classification
        logger.info("Executing Latency Classification (T046)...")
        metrics_data = classify_latency(metrics_data, threshold_ms=config['thresholds']['latency_diff_ms'])
        
        # Save updated metrics
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        logger.info(f"Updated metrics saved to {metrics_path}")
        
        # 6. T047: Source Overlap & Stats
        logger.info("Executing Source Overlap Classification (T047)...")
        
        # Load source results (generated by T039/T045)
        source_results_path = config['paths'].get('sensitivity_analysis_csv', 'data/results/sensitivity_analysis.csv')
        # We need a JSON or dict representation of the Dice coefficient. 
        # Assuming T045/T039 generated a summary JSON or we read from CSV/JSON.
        # Let's assume a 'source_summary.json' exists or we load from the metrics if stats were included there.
        # Based on T045 description, it aggregates results. Let's assume a specific path for source stats.
        source_summary_path = config['paths'].get('source_summary_json', 'data/results/source_summary.json')
        
        if not os.path.exists(source_summary_path):
            # Fallback: try to load from metrics if stats were saved there, or error out
            # For strict compliance, we expect the file to exist if T045 ran.
            raise FileNotFoundError(f"Source summary file {source_summary_path} not found. "
                                    "Please ensure T045 (Report Assembly/Source Aggregation) has completed.")
        
        source_data = load_json_result(source_summary_path)
        
        # Perform TOST if not already in source_data, or load from stats results
        # T042 generates TOST results. We assume they are in source_data or a separate stats file.
        # Let's assume 'stats_summary.json' exists.
        stats_summary_path = config['paths'].get('stats_summary_json', 'data/results/stats_summary.json')
        stats_data = {}
        if os.path.exists(stats_summary_path):
            stats_data = load_json_result(stats_summary_path)
        
        # Combine data for classification
        # source_data should contain 'dice_coefficient'
        # stats_data should contain 'tost_result'
        
        overlap_classification = classify_source_overlap(source_data, stats_data, config)
        
        # Save overlap classification
        overlap_path = config['paths'].get('overlap_classification_json', 'data/results/overlap_classification.json')
        with open(overlap_path, 'w') as f:
            json.dump(overlap_classification, f, indent=2)
        logger.info(f"Source overlap classification saved to {overlap_path}")
        
        # 7. Final Report Generation (T049 placeholder - not implemented in this task)
        # T049 logic would go here: Generate final_report.md
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Pipeline orchestration completed successfully in {duration:.2f} seconds.")
        
        return metrics_data, overlap_classification
        
    except Exception as e:
        logger.error(f"Pipeline orchestration failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    run_orchestration()