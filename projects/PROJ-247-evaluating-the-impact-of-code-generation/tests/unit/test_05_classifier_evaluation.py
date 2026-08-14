import os
import json
import csv
import tempfile
from pathlib import Path
import pytest

# Add code directory to path if running from tests
sys_path = Path(__file__).parent.parent.parent / "code"
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from code_05_classifier_evaluation import calculate_metrics, load_ground_truth_labels, load_predicted_labels

def test_calculate_metrics_precision_recall():
    """
    Test Precision and Recall calculation logic.
    
    Scenario:
    Block 1: GT=LLM, Pred=LLM -> TP
    Block 2: GT=LLM, Pred=Human -> FN
    Block 3: GT=Human, Pred=LLM -> FP
    Block 4: GT=Human, Pred=Human -> TN (ignored in LLM Precision/Recall)
    
    Precision = TP / (TP + FP) = 1 / (1 + 1) = 0.5
    Recall = TP / (TP + FN) = 1 / (1 + 1) = 0.5
    """
    ground_truth = [
        {'block_id': '1', 'label': 'LLM'},
        {'block_id': '2', 'label': 'LLM'},
        {'block_id': '3', 'label': 'HUMAN'},
        {'block_id': '4', 'label': 'HUMAN'},
    ]
    predicted = [
        {'block_id': '1', 'label': 'LLM'},
        {'block_id': '2', 'label': 'HUMAN'},
        {'block_id': '3', 'label': 'LLM'},
        {'block_id': '4', 'label': 'HUMAN'},
    ]
    
    metrics = calculate_metrics(ground_truth, predicted)
    
    assert metrics['precision'] == 0.5
    assert metrics['recall'] == 0.5
    assert metrics['true_positives'] == 1
    assert metrics['false_positives'] == 1
    assert metrics['false_negatives'] == 1
    assert metrics['total_evaluated'] == 4

def test_calculate_metrics_perfect():
    """Test perfect classification."""
    ground_truth = [
        {'block_id': '1', 'label': 'LLM'},
        {'block_id': '2', 'label': 'HUMAN'},
    ]
    predicted = [
        {'block_id': '1', 'label': 'LLM'},
        {'block_id': '2', 'label': 'HUMAN'},
    ]
    
    metrics = calculate_metrics(ground_truth, predicted)
    
    assert metrics['precision'] == 1.0
    assert metrics['recall'] == 1.0
    assert metrics['f1_score'] == 1.0

def test_calculate_metrics_no_tp():
    """Test when there are no True Positives."""
    ground_truth = [
        {'block_id': '1', 'label': 'HUMAN'},
        {'block_id': '2', 'label': 'HUMAN'},
    ]
    predicted = [
        {'block_id': '1', 'label': 'LLM'},
        {'block_id': '2', 'label': 'LLM'},
    ]
    
    metrics = calculate_metrics(ground_truth, predicted)
    
    assert metrics['precision'] == 0.0 # 0 / (0 + 2)
    assert metrics['recall'] == 0.0 # 0 / (0 + 0) -> handled by division by zero check in code? 
    # In code: recall = tp / (tp + fn). If tp=0, fn=0 (since no GT LLM), then 0/0 -> 0.0
    assert metrics['recall'] == 0.0

def test_load_ground_truth_labels_format():
    """Test loading ground truth CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=['block_id', 'ground_truth_label'])
        writer.writeheader()
        writer.writerow({'block_id': '1', 'ground_truth_label': 'LLM'})
        writer.writerow({'block_id': '2', 'ground_truth_label': 'HUMAN'})
        temp_path = f.name
    
    try:
        data = load_ground_truth_labels(temp_path)
        assert len(data) == 2
        assert data[0]['label'] == 'LLM'
        assert data[1]['label'] == 'HUMAN'
    finally:
        os.unlink(temp_path)

def test_load_predicted_labels_format():
    """Test loading predicted CSV."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.DictWriter(f, fieldnames=['block_id', 'predicted_label', 'confidence'])
        writer.writeheader()
        writer.writerow({'block_id': '1', 'predicted_label': 'LLM', 'confidence': '0.95'})
        writer.writerow({'block_id': '2', 'predicted_label': 'HUMAN', 'confidence': '0.80'})
        temp_path = f.name
    
    try:
        data = load_predicted_labels(temp_path)
        assert len(data) == 2
        assert data[0]['label'] == 'LLM'
        assert data[0]['confidence'] == 0.95
    finally:
        os.unlink(temp_path)
