import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple

def setup_output_directories():
    """Ensure all required output directories exist."""
    dirs = [
        "data/ground_truth",
        "data/logs",
        "data/processed"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def load_ground_truth_labels(path: str) -> List[Dict[str, Any]]:
    """
    Load ground truth labels from a CSV file.
    
    Args:
        path: Path to the CSV file containing block_id and true_label.
        
    Returns:
        List of dictionaries with 'block_id' and 'true_label'.
    """
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'block_id': row['block_id'],
                'true_label': row['true_label']
            })
    return data

def load_predicted_labels(path: str) -> List[Dict[str, Any]]:
    """
    Load predicted labels from a CSV file.
    
    Args:
        path: Path to the CSV file containing block_id, predicted_label, and confidence.
        
    Returns:
        List of dictionaries with 'block_id', 'predicted_label', and 'confidence'.
    """
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'block_id': row['block_id'],
                'predicted_label': row['predicted_label'],
                'confidence': float(row['confidence'])
            })
    return data

def calculate_metrics(ground_truth: List[Dict[str, Any]], predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate precision, recall, and other classification metrics.
    
    Args:
        ground_truth: List of dicts with 'block_id' and 'true_label'.
        predictions: List of dicts with 'block_id', 'predicted_label', and 'confidence'.
        
    Returns:
        Dictionary containing TP, FP, FN, TN, precision, recall, and F1 score.
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
        
        if block_id in pred_lookup:
            pred_label = pred_lookup[block_id]['predicted_label']
            
            if true_label == 'LLM' and pred_label == 'LLM':
                tp += 1
            elif true_label == 'Human' and pred_label == 'Human':
                tn += 1
            elif true_label == 'LLM' and pred_label == 'Human':
                fn += 1
            elif true_label == 'Human' and pred_label == 'LLM':
                fp += 1
        else:
            # Block not in predictions (treated as Human prediction for LLM blocks -> FN)
            if true_label == 'LLM':
                fn += 1
            else:
                tn += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn,
        'true_negatives': tn,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'total_samples': len(ground_truth)
    }

def save_metrics(metrics: Dict[str, Any], output_path: str):
    """
    Save metrics to a JSON file.
    
    Args:
        metrics: Dictionary of metrics to save.
        output_path: Path to the output JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

def main():
    """
    Main entry point for classifier evaluation.
    Loads ground truth and predicted labels, calculates metrics, and saves results.
    """
    setup_output_directories()
    
    # Define paths
    ground_truth_path = "data/ground_truth/manual_labels.csv"
    # The predicted labels should come from the tagging step (T013)
    # We assume the tagged blocks are stored in a CSV or we reconstruct them
    # For this task, we assume a file `data/processed/tagged_blocks.csv` exists from T013
    # If that file doesn't exist, we look for a specific predictions file
    predictions_path = "data/processed/tagged_blocks.csv"
    output_path = "data/ground_truth/classifier_metrics.json"
    
    # Check if files exist
    if not os.path.exists(ground_truth_path):
        print(f"Error: Ground truth file not found at {ground_truth_path}")
        sys.exit(1)
        
    if not os.path.exists(predictions_path):
        print(f"Error: Predictions file not found at {predictions_path}")
        sys.exit(1)
    
    # Load data
    print(f"Loading ground truth from {ground_truth_path}...")
    ground_truth = load_ground_truth_labels(ground_truth_path)
    print(f"Loaded {len(ground_truth)} ground truth samples.")
    
    print(f"Loading predictions from {predictions_path}...")
    predictions = load_predicted_labels(predictions_path)
    print(f"Loaded {len(predictions)} predictions.")
    
    # Calculate metrics
    print("Calculating metrics...")
    metrics = calculate_metrics(ground_truth, predictions)
    
    # Save results
    print(f"Saving metrics to {output_path}...")
    save_metrics(metrics, output_path)
    
    print("Evaluation complete.")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1_score']:.4f}")

if __name__ == "__main__":
    main()
