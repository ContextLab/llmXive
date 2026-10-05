import pytest
import os
import json
import csv
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from code_05_classifier_evaluation import calculate_metrics, load_ground_truth_labels, load_predicted_labels

# Mock data for testing
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

def test_calculate_metrics():
    """Test the calculate_metrics function with mock data."""
    metrics = calculate_metrics(MOCK_GROUND_TRUTH, MOCK_PREDICTIONS)
    
    # Expected:
    # TP: block_001 (LLM->LLM), block_005 (LLM->LLM) => 2
    # FP: block_004 (Human->LLM) => 1
    # FN: block_003 (LLM->Human) => 1
    # TN: block_002 (Human->Human) => 1
    
    expected_tp = 2
    expected_fp = 1
    expected_fn = 1
    expected_tn = 1
    
    expected_precision = expected_tp / (expected_tp + expected_fp)  # 2/3
    expected_recall = expected_tp / (expected_tp + expected_fn)     # 2/3
    
    assert metrics['true_positives'] == expected_tp
    assert metrics['false_positives'] == expected_fp
    assert metrics['false_negatives'] == expected_fn
    assert metrics['true_negatives'] == expected_tn
    assert abs(metrics['precision'] - expected_precision) < 1e-6
    assert abs(metrics['recall'] - expected_recall) < 1e-6

def test_load_ground_truth_labels(tmp_path):
    """Test loading ground truth labels from a CSV file."""
    csv_path = tmp_path / "ground_truth.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['block_id', 'true_label'])
        writer.writeheader()
        for item in MOCK_GROUND_TRUTH:
            writer.writerow(item)
    
    loaded = load_ground_truth_labels(str(csv_path))
    assert len(loaded) == len(MOCK_GROUND_TRUTH)
    for i, item in enumerate(loaded):
        assert item['block_id'] == MOCK_GROUND_TRUTH[i]['block_id']
        assert item['true_label'] == MOCK_GROUND_TRUTH[i]['true_label']

def test_load_predicted_labels(tmp_path):
    """Test loading predicted labels from a CSV file."""
    csv_path = tmp_path / "predictions.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['block_id', 'predicted_label', 'confidence'])
        writer.writeheader()
        for item in MOCK_PREDICTIONS:
            writer.writerow(item)
    
    loaded = load_predicted_labels(str(csv_path))
    assert len(loaded) == len(MOCK_PREDICTIONS)
    for i, item in enumerate(loaded):
        assert item['block_id'] == MOCK_PREDICTIONS[i]['block_id']
        assert item['predicted_label'] == MOCK_PREDICTIONS[i]['predicted_label']
        assert item['confidence'] == MOCK_PREDICTIONS[i]['confidence']

def test_edge_case_no_predictions():
    """Test calculate_metrics when there are no predictions."""
    metrics = calculate_metrics(MOCK_GROUND_TRUTH, [])
    
    # All LLM blocks become FN, all Human blocks become TN
    expected_tp = 0
    expected_fp = 0
    expected_fn = 3  # block_001, block_003, block_005
    expected_tn = 2  # block_002, block_004
    
    assert metrics['true_positives'] == expected_tp
    assert metrics['false_positives'] == expected_fp
    assert metrics['false_negatives'] == expected_fn
    assert metrics['true_negatives'] == expected_tn
    assert metrics['precision'] == 0.0
    assert metrics['recall'] == 0.0

def test_edge_case_all_correct():
    """Test calculate_metrics when all predictions are correct."""
    all_correct_predictions = [
        {'block_id': 'block_001', 'predicted_label': 'LLM', 'confidence': 0.95},
        {'block_id': 'block_002', 'predicted_label': 'Human', 'confidence': 0.92},
        {'block_id': 'block_003', 'predicted_label': 'LLM', 'confidence': 0.90},
        {'block_id': 'block_004', 'predicted_label': 'Human', 'confidence': 0.88},
        {'block_id': 'block_005', 'predicted_label': 'LLM', 'confidence': 0.99},
    ]
    metrics = calculate_metrics(MOCK_GROUND_TRUTH, all_correct_predictions)
    
    assert metrics['true_positives'] == 3
    assert metrics['false_positives'] == 0
    assert metrics['false_negatives'] == 0
    assert metrics['true_negatives'] == 2
    assert metrics['precision'] == 1.0
    assert metrics['recall'] == 1.0
