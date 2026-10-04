import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple

def setup_output_directories():
    """Ensure all required output directories exist."""
    output_dirs = [
        Path("data/ground_truth"),
        Path("data/logs"),
        Path("data/processed"),
        Path("docs/paper")
    ]
    for directory in output_dirs:
        directory.mkdir(parents=True, exist_ok=True)

def load_ground_truth_labels(filepath: str) -> List[Dict[str, Any]]:
    """
    Load the ground truth labels from a CSV file.
    Expected columns: block_id, true_label (LLM or Human)
    """
    labels = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            labels.append({
                'block_id': row['block_id'],
                'true_label': row['true_label']
            })
    return labels

def load_predicted_labels(filepath: str) -> List[Dict[str, Any]]:
    """
    Load the predicted labels from the tagged code blocks CSV.
    Expected columns: block_id, predicted_label (LLM or Human), confidence
    """
    predictions = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            predictions.append({
                'block_id': row['block_id'],
                'predicted_label': row['predicted_label'],
                'confidence': float(row['confidence'])
            })
    return predictions

def calculate_metrics(ground_truth: List[Dict], predictions: List[Dict]) -> Dict[str, Any]:
    """
    Calculate precision and recall for the classifier.
    
    Precision = TP / (TP + FP)
    Recall = TP / (TP + FN)
    
    We treat 'LLM' as the positive class.
    """
    # Create a lookup for predictions by block_id
    pred_lookup = {p['block_id']: p for p in predictions}
    
    tp = 0
    fp = 0
    fn = 0
    tn = 0
    
    for gt in ground_truth:
        block_id = gt['block_id']
        true_label = gt['true_label']
        
        if block_id not in pred_lookup:
            # Block was not predicted (e.g., excluded due to low confidence)
            # If it was truly LLM, it's a False Negative. If Human, True Negative.
            if true_label == 'LLM':
                fn += 1
            else:
                tn += 1
            continue
        
        pred_label = pred_lookup[block_id]['predicted_label']
        
        if true_label == 'LLM' and pred_label == 'LLM':
            tp += 1
        elif true_label == 'Human' and pred_label == 'LLM':
            fp += 1
        elif true_label == 'LLM' and pred_label == 'Human':
            fn += 1
        elif true_label == 'Human' and pred_label == 'Human':
            tn += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'true_negatives': tn,
        'total_evaluated': len(ground_truth)
    }

def save_metrics(metrics: Dict[str, Any], output_path: str):
    """Save the calculated metrics to a JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4)

def main():
    """
    Main entry point for classifier evaluation.
    Reads ground truth and predictions, calculates metrics, and saves results.
    """
    setup_output_directories()
    
    # Define paths based on project structure
    ground_truth_path = Path("data/ground_truth/manual_labels.csv")
    # The predictions come from the tagged blocks file generated in T013
    # Assuming it's saved in data/processed or data/raw. 
    # Based on T013 description: "tag blocks... Log exclusions". 
    # Usually tagged blocks are saved to a CSV. Let's assume data/processed/tagged_blocks.csv
    # or data/raw/tagged_blocks.csv. The task T013 says "Output: Append metrics to data/raw/code_blocks.csv" 
    # but T015 says "load block_metrics". 
    # Let's assume the tagged data is in data/processed/tagged_blocks.csv as per typical pipeline flow 
    # after filtering. If not, we might need to look at data/raw.
    # However, T017a says "save to data/ground_truth/manual_labels.csv".
    # T017b says "comparing predicted labels (from T013)".
    # T013 output is likely the tagged blocks. Let's assume a standard location.
    # If the pipeline saves tagged blocks to data/processed/tagged_blocks.csv, we use that.
    # If not, we might need to check data/raw/code_blocks.csv if it was updated.
    # But T014 appends metrics to code_blocks.csv. T013 tags blocks.
    # Let's assume the tagged data is saved in a separate file or updated in code_blocks.csv.
    # For safety, let's assume the tagged data is in data/processed/tagged_blocks.csv.
    # If that doesn't exist, we might need to check data/raw/code_blocks.csv.
    # But the task says "comparing predicted labels (from T013)".
    # Let's assume the predictions are in data/processed/tagged_blocks.csv.
    # If not, we might need to adjust.
    # Let's try data/processed/tagged_blocks.csv first.
    predictions_path = Path("data/processed/tagged_blocks.csv")
    
    if not predictions_path.exists():
        # Fallback to data/raw/code_blocks.csv if tagged_blocks.csv doesn't exist
        # This might happen if T013 updated code_blocks.csv directly.
        predictions_path = Path("data/raw/code_blocks.csv")
    
    if not ground_truth_path.exists():
        print(f"Error: Ground truth file not found at {ground_truth_path}")
        sys.exit(1)
    
    if not predictions_path.exists():
        print(f"Error: Predictions file not found at {predictions_path}")
        sys.exit(1)
    
    print(f"Loading ground truth from {ground_truth_path}")
    ground_truth = load_ground_truth_labels(str(ground_truth_path))
    
    print(f"Loading predictions from {predictions_path}")
    predictions = load_predicted_labels(str(predictions_path))
    
    print(f"Calculating metrics for {len(ground_truth)} blocks")
    metrics = calculate_metrics(ground_truth, predictions)
    
    output_path = Path("data/ground_truth/classifier_metrics.json")
    save_metrics(metrics, str(output_path))
    
    print(f"Metrics saved to {output_path}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")

if __name__ == "__main__":
    main()
