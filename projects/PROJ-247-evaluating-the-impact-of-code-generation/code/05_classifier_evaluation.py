import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

def setup_output_directories():
    """Ensure output directories exist."""
    output_dir = project_root / "data" / "ground_truth"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_ground_truth_labels(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load ground truth labels from manual_labels.csv.
    
    Expected columns: block_id, label (LLM/Human)
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {file_path}")
    
    labels = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize label to uppercase for consistency
            row['label'] = row['label'].strip().upper()
            if row['label'] not in ('LLM', 'HUMAN'):
                logger.warning(f"Invalid label in ground truth: {row['label']} for block {row.get('block_id')}")
                continue
            labels.append(row)
    
    logger.info(f"Loaded {len(labels)} ground truth labels from {file_path}")
    return labels

def load_predicted_labels(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load predicted labels from the blocks CSV generated during curation.
    We assume the file 'data/processed/blocks.csv' or similar exists 
    containing the classifier predictions.
    
    If the specific file isn't found, we look for the most recent blocks file.
    """
    # Try to find the blocks file in data/processed
    processed_dir = project_root / "data" / "processed"
    blocks_file = processed_dir / "blocks.csv"
    
    if not blocks_file.exists():
        # Fallback: search for any blocks*.csv in processed
        candidates = list(processed_dir.glob("blocks*.csv"))
        if not candidates:
            raise FileNotFoundError(
                f"Predicted labels file not found. Expected {blocks_file} or any blocks*.csv in {processed_dir}"
            )
        # Sort by modification time, take most recent
        blocks_file = max(candidates, key=lambda p: p.stat().st_mtime)
        logger.info(f"Using found blocks file: {blocks_file}")
    
    predictions = []
    with open(blocks_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # We expect columns: block_id, predicted_label, confidence
            if 'block_id' not in row or 'predicted_label' not in row:
                continue
            
            pred_label = row['predicted_label'].strip().upper()
            if pred_label not in ('LLM', 'HUMAN'):
                continue
            
            predictions.append({
                'block_id': row['block_id'],
                'predicted_label': pred_label,
                'confidence': float(row.get('confidence', 0.0))
            })
    
    logger.info(f"Loaded {len(predictions)} predicted labels from {blocks_file}")
    return predictions

def calculate_metrics(ground_truth: List[Dict], predictions: List[Dict]) -> Dict[str, Any]:
    """
    Calculate precision, recall, and F1 score for the classifier.
    
    We treat 'LLM' as the positive class.
    """
    # Create lookup dictionaries
    gt_dict = {item['block_id']: item['label'] for item in ground_truth}
    pred_dict = {item['block_id']: item['predicted_label'] for item in predictions}
    
    # Only evaluate blocks that appear in both ground truth and predictions
    common_ids = set(gt_dict.keys()) & set(pred_dict.keys())
    
    if not common_ids:
        raise ValueError("No common block IDs between ground truth and predictions.")
    
    # Confusion matrix components (Positive = LLM)
    tp = 0  # True Positive: Actual LLM, Predicted LLM
    fp = 0  # False Positive: Actual Human, Predicted LLM
    fn = 0  # False Negative: Actual LLM, Predicted Human
    tn = 0  # True Negative: Actual Human, Predicted Human
    
    for bid in common_ids:
        actual = gt_dict[bid]
        predicted = pred_dict[bid]
        
        if actual == 'LLM' and predicted == 'LLM':
            tp += 1
        elif actual == 'HUMAN' and predicted == 'LLM':
            fp += 1
        elif actual == 'LLM' and predicted == 'HUMAN':
            fn += 1
        elif actual == 'HUMAN' and predicted == 'HUMAN':
            tn += 1
    
    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(common_ids) if len(common_ids) > 0 else 0.0
    
    metrics = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "accuracy": round(accuracy, 4),
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn
        },
        "sample_size": len(common_ids),
        "positive_class": "LLM",
        "description": "Classifier performance on ground truth subset selected in T017a"
    }
    
    logger.info(f"Calculated metrics: Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
    return metrics

def save_metrics(metrics: Dict[str, Any], output_path: Path):
    """Save metrics to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved classifier metrics to {output_path}")

def main():
    """Main entry point for classifier evaluation."""
    logger.info("Starting T017b: Classifier Evaluation")
    
    # Setup directories
    output_dir = setup_output_directories()
    metrics_file = output_dir / "classifier_metrics.json"
    gt_file = project_root / "data" / "ground_truth" / "manual_labels.csv"
    
    # Load data
    try:
        ground_truth = load_ground_truth_labels(gt_file)
        predictions = load_predicted_labels(project_root / "data" / "processed")
    except FileNotFoundError as e:
        logger.error(str(e))
        # Re-raise to fail loudly as per constraints
        raise e
    
    # Calculate metrics
    metrics = calculate_metrics(ground_truth, predictions)
    
    # Save results
    save_metrics(metrics, metrics_file)
    
    logger.info("T017b completed successfully.")
    return metrics

if __name__ == "__main__":
    main()
