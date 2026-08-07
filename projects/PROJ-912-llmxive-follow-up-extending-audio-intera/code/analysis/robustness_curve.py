import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_path_config, get_evaluation_config
from utils.logger import get_logger, LlmXiveError

logger = get_logger(__name__)

def load_robustness_metrics(metrics_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load robustness metrics from CSV."""
    if metrics_path is None:
        path_config = get_path_config()
        metrics_path = path_config.processed_dir / "robustness_metrics.csv"
    
    if not metrics_path.exists():
        raise LlmXiveError(f"Robustness metrics file not found: {metrics_path}")
    
    results = []
    with open(metrics_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            try:
                row['auc'] = float(row['auc'])
                row['latency_ms'] = float(row['latency_ms'])
                row['ram_gb'] = float(row['ram_gb'])
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping row due to conversion error: {e}")
                continue
            results.append(row)
    
    if not results:
        raise LlmXiveError("Robustness metrics file is empty or contains no valid rows.")
    
    return results

def extract_compression_metadata(model_id: str) -> Dict[str, Any]:
    """Extract compression metadata (bit-width, params) from model_id string."""
    # Expected format: "model_{precision}_pruned_{ratio}" or similar
    # Examples: "wav2vec2_fp32", "wav2vec2_int8_pruned_0.1", "wav2vec2_int4"
    metadata = {
        'bit_width': 32,
        'pruning_ratio': 0.0,
        'model_id': model_id
    }
    
    if 'int4' in model_id.lower():
        metadata['bit_width'] = 4
    elif 'int8' in model_id.lower():
        metadata['bit_width'] = 8
    elif 'fp32' in model_id.lower():
        metadata['bit_width'] = 32
    
    # Try to extract pruning ratio if present
    if 'pruned' in model_id.lower():
        parts = model_id.lower().split('pruned_')
        if len(parts) > 1:
            try:
                metadata['pruning_ratio'] = float(parts[1])
            except ValueError:
                pass
    
    return metadata

def compute_correlation_data(metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute correlation data (compression vs AUC) from metrics."""
    correlation_data = []
    
    for row in metrics:
        model_id = row.get('model_id', 'unknown')
        auc = row.get('auc', 0.0)
        
        meta = extract_compression_metadata(model_id)
        
        entry = {
            'model_id': model_id,
            'bit_width': meta['bit_width'],
            'pruning_ratio': meta['pruning_ratio'],
            'auc': auc,
            'latency_ms': row.get('latency_ms', 0.0),
            'ram_gb': row.get('ram_gb', 0.0)
        }
        correlation_data.append(entry)
    
    # Sort by bit_width descending (highest precision first) to establish baseline
    correlation_data.sort(key=lambda x: (-x['bit_width'], x['pruning_ratio']))
    
    return correlation_data

def validate_correlation_data(data: List[Dict[str, Any]]) -> bool:
    """Validate that correlation data has required fields and reasonable values."""
    if not data:
        raise LlmXiveError("Correlation data cannot be empty.")
    
    required_fields = {'model_id', 'bit_width', 'auc'}
    for entry in data:
        if not required_fields.issubset(entry.keys()):
            raise LlmXiveError(f"Missing required fields in data: {entry.keys()}")
        if not (0.0 <= entry['auc'] <= 1.0):
            logger.warning(f"AUC out of range [0, 1] for {entry['model_id']}: {entry['auc']}")
    
    return True

def save_correlation_data(data: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """Save correlation data to JSON."""
    if output_path is None:
        path_config = get_path_config()
        output_path = path_config.processed_dir / "correlation_data.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved correlation data to {output_path}")
    return output_path

def load_correlation_data(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load correlation data from JSON."""
    if input_path is None:
        path_config = get_path_config()
        input_path = path_config.processed_dir / "correlation_data.json"
    
    if not input_path.exists():
        raise LlmXiveError(f"Correlation data file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise LlmXiveError("Correlation data must be a list of records.")
    
    return data

def detect_step_change(correlation_data: List[Dict[str, Any]], threshold_percent: float = 10.0) -> Dict[str, Any]:
    """
    Detect the 'breaking point' where relative AUC drop exceeds threshold_percent.
    
    Args:
        correlation_data: List of records with bit_width and auc.
        threshold_percent: The percentage drop threshold (default 10.0).
    
    Returns:
        Dict with bit-width, drop %, and threshold_violated flag.
    """
    if not correlation_data:
        raise LlmXiveError("Cannot detect step change in empty data.")
    
    # Sort by bit_width descending to start from highest precision (baseline)
    sorted_data = sorted(correlation_data, key=lambda x: -x['bit_width'])
    
    # Use the first entry (highest bit-width) as the baseline AUC
    baseline = sorted_data[0]
    baseline_auc = baseline['auc']
    baseline_bit_width = baseline['bit_width']
    
    logger.info(f"Baseline AUC: {baseline_auc:.4f} at bit-width {baseline_bit_width}")
    
    breaking_point = None
    threshold_violated = False
    
    for entry in sorted_data[1:]:
        current_auc = entry['auc']
        current_bit_width = entry['bit_width']
        
        # Calculate relative drop
        if baseline_auc == 0:
            drop_percent = 0.0
        else:
            drop_percent = ((baseline_auc - current_auc) / baseline_auc) * 100.0
        
        logger.debug(f"Checking {entry['model_id']}: bit={current_bit_width}, auc={current_auc:.4f}, drop={drop_percent:.2f}%")
        
        if drop_percent > threshold_percent:
            breaking_point = {
                'bit_width': current_bit_width,
                'baseline_auc': baseline_auc,
                'current_auc': current_auc,
                'drop_percent': drop_percent,
                'model_id': entry['model_id'],
                'threshold_violated': True
            }
            threshold_violated = True
            logger.info(f"Breaking point detected at bit-width {current_bit_width}: drop {drop_percent:.2f}% > {threshold_percent}%")
            break
    
    if not breaking_point:
        # No breaking point found; the drop never exceeded threshold
        breaking_point = {
            'bit_width': sorted_data[-1]['bit_width'], # Report the lowest bit-width checked
            'baseline_auc': baseline_auc,
            'current_auc': sorted_data[-1]['auc'],
            'drop_percent': ((baseline_auc - sorted_data[-1]['auc']) / baseline_auc * 100.0) if baseline_auc > 0 else 0.0,
            'model_id': sorted_data[-1]['model_id'],
            'threshold_violated': False
        }
        logger.info(f"No breaking point detected. Max drop was {breaking_point['drop_percent']:.2f}% <= {threshold_percent}%")
    
    return breaking_point

def save_breaking_point(breaking_point: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Save breaking point analysis to JSON."""
    if output_path is None:
        path_config = get_path_config()
        output_path = path_config.processed_dir / "breaking_point.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(breaking_point, f, indent=2)
    
    logger.info(f"Saved breaking point analysis to {output_path}")
    return output_path

def run_analysis() -> Dict[str, Any]:
    """
    Main analysis pipeline for T030: Step-change detection.
    1. Load correlation_data.json (from T029)
    2. Detect breaking point (>10% AUC drop)
    3. Save breaking_point.json
    """
    path_config = get_path_config()
    eval_config = get_evaluation_config()
    
    # Load correlation data
    correlation_path = path_config.processed_dir / "correlation_data.json"
    logger.info(f"Loading correlation data from {correlation_path}")
    correlation_data = load_correlation_data(correlation_path)
    
    # Validate
    validate_correlation_data(correlation_data)
    
    # Detect step change
    threshold = eval_config.get('auc_drop_threshold_percent', 10.0)
    logger.info(f"Detecting step change with threshold: {threshold}%")
    breaking_point = detect_step_change(correlation_data, threshold_percent=threshold)
    
    # Save result
    output_path = save_breaking_point(breaking_point)
    
    return {
        'status': 'success',
        'breaking_point': breaking_point,
        'output_file': str(output_path)
    }

def main():
    """Entry point for script execution."""
    try:
        result = run_analysis()
        print(json.dumps(result, indent=2))
        logger.info("Step-change detection completed successfully.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()