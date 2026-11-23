import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("llmXive.utils.join_utils")

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file into a list of dictionaries."""
    data = []
    if not Path(path).exists():
        logger.error(f"File not found: {path}")
        return data
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed JSON line in {path}: {e}")
    return data

def save_jsonl(data: List[Dict[str, Any]], path: str):
    """Save a list of dictionaries to a JSONL file."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    logger.info(f"Saved {len(data)} records to {path}")

def join_ground_truth_and_features(
    ground_truth_path: str,
    feature_path: str,
    output_path: str,
    id_field: str = "sample_id"
) -> Dict[str, Any]:
    """
    Join ground truth and feature datasets on sample_id.
    
    Filters for samples that have both Features and Ground Truth.
    Excludes OOM sweep failures (where B* might be None or specific error code).
    
    Args:
        ground_truth_path: Path to ground_truth.jsonl
        feature_path: Path to features.jsonl
        output_path: Path to write training_set.jsonl
        id_field: The key used to join records
    
    Returns:
        Summary statistics of the join operation.
    """
    logger.info(f"Joining {ground_truth_path} and {feature_path}")
    
    gt_data = load_jsonl(ground_truth_path)
    feat_data = load_jsonl(feature_path)
    
    if not gt_data:
        logger.error("Ground truth data is empty. Cannot join.")
        return {"status": "failed", "reason": "empty_ground_truth"}
    
    if not feat_data:
        logger.error("Feature data is empty. Cannot join.")
        return {"status": "failed", "reason": "empty_features"}
    
    # Index features by ID for O(1) lookup
    feat_index = {item[id_field]: item for item in feat_data if id_field in item}
    gt_index = {item[id_field]: item for item in gt_data if id_field in item}
    
    joined_data = []
    skipped_gt = 0
    skipped_feat = 0
    oom_skipped = 0
    
    for sample_id, gt_record in gt_index.items():
        if sample_id not in feat_index:
            skipped_gt += 1
            continue
        
        feat_record = feat_index[sample_id]
        
        # Check for OOM failures in ground truth (e.g., B* is None or specific error flag)
        # Assuming B* is stored as 'optimal_block_size' or similar. 
        # If the sweep failed for this sample, it might not have a valid B*.
        # We need to check the schema. Assuming 'optimal_block_size' is the key.
        b_star = gt_record.get('optimal_block_size')
        if b_star is None:
            oom_skipped += 1
            continue
        
        # Merge records
        merged = {
            "sample_id": sample_id,
            "ground_truth": gt_record,
            "features": feat_record
        }
        # Flatten if preferred, but keeping nested structure is safer for schema
        # merged = {**gt_record, **feat_record} 
        joined_data.append(merged)
    
    save_jsonl(joined_data, output_path)
    
    result = {
        "status": "completed",
        "total_gt": len(gt_data),
        "total_feat": len(feat_data),
        "joined": len(joined_data),
        "skipped_missing_feat": skipped_gt,
        "skipped_oom": oom_skipped
    }
    
    logger.info(f"Join completed. Result: {result}")
    return result

def join_uncertainty_metrics(
    training_set_path: str,
    uncertainty_path: str,
    output_path: str,
    id_field: str = "sample_id"
) -> Dict[str, Any]:
    """
    Join training set with uncertainty metrics.
    """
    logger.info(f"Joining training set with uncertainty metrics: {uncertainty_path}")
    
    train_data = load_jsonl(training_set_path)
    unc_data = load_jsonl(uncertainty_path)
    
    if not train_data:
        return {"status": "failed", "reason": "empty_training_set"}
    
    unc_index = {item[id_field]: item for item in unc_data if id_field in item}
    
    joined_data = []
    skipped = 0
    
    for record in train_data:
        sample_id = record.get(id_field)
        if sample_id and sample_id in unc_index:
            record["uncertainty"] = unc_index[sample_id]
            joined_data.append(record)
        else:
            skipped += 1
    
    save_jsonl(joined_data, output_path)
    
    return {
        "status": "completed",
        "total": len(train_data),
        "joined": len(joined_data),
        "skipped_missing_unc": skipped
    }