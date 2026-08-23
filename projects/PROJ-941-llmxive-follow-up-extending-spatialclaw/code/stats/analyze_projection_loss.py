"""
Projection Loss Analysis Module for SpatialClaw Benchmark.

This module extracts and saves specific geometric parameters for tasks where
"projection loss" (information lost in 2D projection) is the primary cause of
failure for the 2D agent, compared to the 3D baseline.

It relies on the classification logic from T059 and the final paired dataset
from T047.
"""
import json
import os
import logging
import argparse
from typing import Dict, List, Any, Optional, Tuple
from data.loader import load_dataset, DataLoadError
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PAIRED_DATASET_PATH = "results/analysis/final_paired_dataset.csv"
RAW_DATASET_PATH = "data/raw/synthetic_spatialclaw_v1.json"
FAILURE_ANALYSIS_LOG_PATH = "results/logs/failure_analysis.log"
CASE_STUDY_OUTPUT_PATH = "results/analysis/projection_loss_case_studies.json"
FLAT_OBJECT_THRESHOLD = 0.01  # Epsilon for zero depth variance

def load_json_file(path: str) -> List[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_paired_dataset(path: str) -> List[Dict[str, Any]]:
    """
    Load the final paired dataset CSV.
    Returns a list of dicts.
    """
    import csv
    if not os.path.exists(path):
        raise FileNotFoundError(f"Paired dataset not found: {path}")
    
    data = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings back to float/int
            for key, value in row.items():
                if key in ['2d_success_rate', '2d_mean_latency', '3d_latency', 'success_diff', 'latency_diff']:
                    row[key] = float(value)
                elif key in ['3d_success']:
                    row[key] = int(value)
            data.append(row)
    return data

def load_raw_dataset(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load the raw synthetic dataset and index by task_id.
    """
    try:
        dataset = load_dataset(path)
        # load_dataset returns a list, we need a dict for O(1) lookup
        return {task['task_id']: task for task in dataset}
    except DataLoadError as e:
        logger.error(f"Failed to load raw dataset: {e}")
        raise

def load_failure_analysis_log(path: str) -> Dict[str, str]:
    """
    Load the failure analysis log (JSON lines) and return a dict mapping
    task_id to failure reason.
    """
    failure_map = {}
    if not os.path.exists(path):
        logger.warning(f"Failure analysis log not found: {path}. Assuming no classified failures.")
        return failure_map
    
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                task_id = entry.get('task_id')
                reason = entry.get('reason')
                if task_id and reason:
                    failure_map[task_id] = reason
            except json.JSONDecodeError:
                logger.warning(f"Skipping invalid JSON line in failure log: {line}")
    
    return failure_map

def classify_failure_reason(task_id: str, result_2d: Dict[str, Any], result_3d: Dict[str, Any], gt: Dict[str, Any]) -> str:
    """
    Classify the reason for a 2D agent failure.
    
    Returns:
        str: One of "projection_loss", "action_restriction", or "other".
    
    Logic:
        - If 3D baseline succeeded (3d_success == 1) and 2D agent failed (2d_success_rate == 0.0 or low),
          and the task involves depth/occlusion, it's likely projection loss.
        - If the task is a "flat object" (zero depth variance), and 3D succeeded but 2D failed,
          it is explicitly "projection_loss" as per T045/T059 logic.
        - If 3D also failed, it might be "other" or inherent task difficulty.
        - If 2D failed but 3D succeeded on a non-flat task, check if it's an occlusion/depth task.
    """
    # Determine if 2D failed and 3D succeeded
    # 2d_success_rate is a float between 0 and 1 (averaged over runs)
    # 3d_success is an integer (0 or 1)
    d_failed = result_2d.get('2d_success_rate', 1.0) < 0.5 # Assuming < 50% success is a failure
    d_succeeded = result_3d.get('3d_success', 0) == 1

    if not d_failed:
        return "none" # Not a failure case

    if not d_succeeded:
        return "other" # Both failed, or 3D failed

    # At this point: 2D failed, 3D succeeded.
    task_type = result_2d.get('task_type', '').lower()
    gt_params = gt.get('ground_truth_3d_params', {})
    
    # Check for flat object (zero depth variance)
    # Variance is calculated in T006a/b logic, stored in gt_params if available,
    # or we can infer from coordinates if variance isn't stored.
    # Let's assume 'gt_3d_is_occluded' and task_type are primary indicators.
    # For flat objects, we explicitly check depth variance if stored, or infer from Z coords.
    
    is_flat = False
    if 'depth_variance' in gt_params:
        if gt_params['depth_variance'] < FLAT_OBJECT_THRESHOLD:
            is_flat = True
    else:
        # Fallback: check if all Z coords are effectively 0
        # This is a heuristic if variance isn't stored
        objects = gt_params.get('objects', [])
        if objects:
            z_coords = []
            for obj in objects:
                if 'vertices' in obj:
                    for v in obj['vertices']:
                        if 'z' in v:
                            z_coords.append(v['z'])
            if z_coords:
                # Simple variance check
                mean_z = sum(z_coords) / len(z_coords)
                variance = sum((z - mean_z)**2 for z in z_coords) / len(z_coords)
                if variance < FLAT_OBJECT_THRESHOLD:
                    is_flat = True

    if is_flat:
        return "projection_loss"
    
    if task_type in ['occlusion', 'depth']:
        return "projection_loss"
    
    return "action_restriction"

def run_projection_loss_analysis(
    paired_path: str = PAIRED_DATASET_PATH,
    raw_path: str = RAW_DATASET_PATH,
    failure_log_path: str = FAILURE_ANALYSIS_LOG_PATH,
    output_path: str = CASE_STUDY_OUTPUT_PATH
) -> Dict[str, Any]:
    """
    Main analysis function.
    
    1. Load paired dataset.
    2. Load raw dataset for geometric parameters.
    3. Load existing failure log if present (from T045/T059).
    4. Identify tasks where 2D failed and 3D succeeded.
    5. Classify failure reason.
    6. Filter for "projection_loss".
    7. Extract geometric parameters for a representative subset.
    8. Save to JSON.
    """
    logger.info(f"Starting projection loss case study extraction.")
    logger.info(f"Loading paired dataset from {paired_path}")
    paired_data = load_paired_dataset(paired_path)
    
    logger.info(f"Loading raw dataset from {raw_path}")
    raw_data = load_raw_dataset(raw_path)
    
    logger.info(f"Loading failure analysis log from {failure_log_path}")
    failure_map = load_failure_analysis_log(failure_log_path)
    
    projection_loss_cases = []
    total_candidates = 0
    total_classified = 0

    for row in paired_data:
        task_id = row.get('task_id')
        if not task_id or task_id not in raw_data:
            logger.warning(f"Task {task_id} not found in raw dataset.")
            continue
        
        total_candidates += 1
        
        # Check if 2D failed and 3D succeeded
        d_success = float(row.get('2d_success_rate', 1.0))
        d_baseline_success = int(row.get('3d_success', 0))
        
        if d_success >= 0.5: # 2D succeeded
            continue
        if d_baseline_success == 0: # 3D failed
            continue
        
        # We have a candidate: 2D failed, 3D succeeded
        gt = raw_data[task_id]
        
        # Determine reason
        # Prefer existing log if available, otherwise classify
        reason = failure_map.get(task_id)
        if not reason:
            reason = classify_failure_reason(task_id, row, row, gt)
            total_classified += 1
            # Log to failure analysis log if we classified it now
            # (In a real pipeline, this would be done by T045, but we ensure it here)
            log_entry = {
                "task_id": task_id,
                "reason": reason,
                "2d_success": d_success,
                "3d_success": d_baseline_success
            }
            # Append to log file (ensure directory exists)
            os.makedirs(os.path.dirname(failure_log_path), exist_ok=True)
            with open(failure_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        if reason == "projection_loss":
            # Extract geometric parameters
            # We need a representative subset. Let's take all for now, 
            # or limit to first N if too many.
            case_study = {
                "task_id": task_id,
                "task_type": row.get('task_type'),
                "2d_success_rate": d_success,
                "3d_success": d_baseline_success,
                "failure_reason": reason,
                "geometric_parameters": gt.get('ground_truth_3d_params', {}),
                "seed": gt.get('seed')
            }
            projection_loss_cases.append(case_study)

    logger.info(f"Total candidates (2D fail, 3D pass): {total_candidates}")
    logger.info(f"Newly classified: {total_classified}")
    logger.info(f"Projection loss cases identified: {len(projection_loss_cases)}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    output_data = {
        "total_projection_loss_cases": len(projection_loss_cases),
        "cases": projection_loss_cases,
        "analysis_timestamp": str(os.path.getmtime(paired_path)) if os.path.exists(paired_path) else "unknown"
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Case studies saved to {output_path}")
    return output_data

def main():
    parser = argparse.ArgumentParser(description="Extract projection loss case studies.")
    parser.add_argument('--paired-dataset', type=str, default=PAIRED_DATASET_PATH, help='Path to paired dataset CSV')
    parser.add_argument('--raw-dataset', type=str, default=RAW_DATASET_PATH, help='Path to raw dataset JSON')
    parser.add_argument('--failure-log', type=str, default=FAILURE_ANALYSIS_LOG_PATH, help='Path to failure analysis log')
    parser.add_argument('--output', type=str, default=CASE_STUDY_OUTPUT_PATH, help='Path to output JSON')
    
    args = parser.parse_args()
    
    try:
        run_projection_loss_analysis(
            paired_path=args.paired_dataset,
            raw_path=args.raw_dataset,
            failure_log_path=args.failure_log,
            output_path=args.output
        )
        logger.info("Analysis completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()