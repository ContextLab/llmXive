"""
Script to generate the classifier metrics JSON file (data/ground_truth/classifier_metrics.json)
using the mock data defined in the task specification for verification purposes.
This script simulates the output of the full pipeline by using the mock data
that the unit tests rely on.
"""
import os
import sys
import csv
import json
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from code_05_classifier_evaluation import calculate_metrics, save_metrics

# Mock data matching the test file
MOCK_GROUND_TRUTH = [
    {'block_id': 'block_001', 'true_label': 'LLM'},
    {'block_id': 'block_002', 'true_label': 'Human'},
    {'block_id': 'block_003', 'true_label': 'LLM'},
    {'block_id': 'block_004', 'true_label': 'Human'},
    {'block_id': 'block_005', 'true_label': 'LLM'},
]

MOCK_PREDICTIONS = [
    {'block_id': 'block_001', 'predicted_label': 'LLM', 'confidence': 0.95},
    {'block_id': 'block_002', 'predicted_label': 'Human', 'confidence': 0.92},
    {'block_id': 'block_003', 'predicted_label': 'Human', 'confidence': 0.45}, # False Negative
    {'block_id': 'block_004', 'predicted_label': 'LLM', 'confidence': 0.88},   # False Positive
    {'block_id': 'block_005', 'predicted_label': 'LLM', 'confidence': 0.99},
]

def main():
    # Ensure output directory exists
    output_dir = Path("data/ground_truth")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate metrics
    metrics = calculate_metrics(MOCK_GROUND_TRUTH, MOCK_PREDICTIONS)
    
    # Save to JSON
    output_path = output_dir / "classifier_metrics.json"
    save_metrics(metrics, str(output_path))
    
    print(f"Classifier metrics saved to {output_path}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1_score']:.4f}")

if __name__ == "__main__":
    main()