"""
Classifier Evaluation Module (T017b)

Calculates precision and recall for the CodeBERT classifier by comparing
predicted labels against ground truth manual labels.
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import get_logger
from utils.models import LabelType

logger = get_logger(__name__)

def setup_output_directories():
    """Ensure output directories exist."""
    output_dir = Path("data/ground_truth")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_ground_truth_labels(file_path: str) -> List[Dict[str, Any]]:
    """
    Load ground truth labels from CSV.
    Expected columns: block_id, manual_label
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Ground truth file not found: {file_path}")

    results = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'block_id': row['block_id'],
                'manual_label': row['manual_label']
            })
    return results

def load_predicted_labels(tagger_output_path: str) -> Dict[str, str]:
    """
    Load predicted labels from the tagged blocks output.
    We assume the output of T013 (tag_blocks_with_classifier) is a CSV
    containing block_id and predicted_label (or similar).
    """
    if not os.path.exists(tagger_output_path):
        raise FileNotFoundError(f"Predicted labels file not found: {tagger_output_path}")

    predictions = {}
    with open(tagger_output_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names if necessary
            block_id = row.get('block_id') or row.get('id')
            pred_label = row.get('predicted_label') or row.get('label')
            if block_id and pred_label:
                predictions[block_id] = pred_label
    return predictions

def calculate_metrics(
    ground_truth: List[Dict[str, Any]],
    predictions: Dict[str, str]
) -> Dict[str, float]:
    """
    Calculate Precision and Recall for the classifier.

    Precision = TP / (TP + FP)
    Recall = TP / (TP + FN)

    We evaluate specifically for the 'LLM' class (positive class).
    """
    tp = 0
    fp = 0
    fn = 0

    for item in ground_truth:
        block_id = item['block_id']
        true_label = item['manual_label']

        if block_id not in predictions:
            # If we have no prediction for a ground truth item, treat as FN (missed detection)
            # or exclude? Usually exclude if missing, but let's count as FN for recall.
            # However, typically ground truth subset is a subset of tagged blocks.
            # If it's missing from predictions, it might be because it was filtered out.
            # For this task, we assume all ground truth items were tagged.
            continue

        pred_label = predictions[block_id]

        # Normalize labels to ensure case-insensitivity
        true_label = true_label.strip().upper()
        pred_label = pred_label.strip().upper()

        if true_label == 'LLM':
            if pred_label == 'LLM':
                tp += 1
            else:
                fn += 1
        elif true_label == 'HUMAN':
            if pred_label == 'LLM':
                fp += 1
            # else: TN, ignored for precision/recall of positive class

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "total_evaluated": len(ground_truth)
    }

def save_metrics(metrics: Dict[str, Any], output_path: str):
    """Save metrics to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {output_path}")

def main():
    """
    Main entry point for T017b.
    1. Load ground truth from data/ground_truth/manual_labels.csv
    2. Load predictions from data/processed/tagged_blocks.csv (output of T013)
    3. Calculate precision/recall
    4. Save to data/ground_truth/classifier_metrics.json
    """
    logger.info("Starting Classifier Evaluation (T017b)...")

    # Setup paths
    gt_path = "data/ground_truth/manual_labels.csv"
    pred_path = "data/processed/tagged_blocks.csv" # Assumed output of T013
    output_path = "data/ground_truth/classifier_metrics.json"

    output_dir = setup_output_directories()

    try:
        # Load data
        logger.info(f"Loading ground truth from {gt_path}")
        ground_truth = load_ground_truth_labels(gt_path)
        logger.info(f"Loaded {len(ground_truth)} ground truth items.")

        logger.info(f"Loading predictions from {pred_path}")
        predictions = load_predicted_labels(pred_path)
        logger.info(f"Loaded {len(predictions)} predictions.")

        # Calculate metrics
        logger.info("Calculating metrics...")
        metrics = calculate_metrics(ground_truth, predictions)

        # Save results
        save_metrics(metrics, output_path)

        logger.info(f"Evaluation complete. Precision: {metrics['precision']}, Recall: {metrics['recall']}")
        return metrics

    except FileNotFoundError as e:
        logger.error(f"Required data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        raise

if __name__ == "__main__":
    main()
