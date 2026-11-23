"""
Unit tests for T019 benchmark result generation logic.
"""
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from benchmark.generate_benchmark_results import (
    calculate_exact_match, 
    calculate_f1_score, 
    compute_row_metrics,
    load_csv_as_dict
)

def test_exact_match_true():
    assert calculate_exact_match("A", "A") is True
    assert calculate_exact_match(" A ", "a") is True

def test_exact_match_false():
    assert calculate_exact_match("A", "B") is False
    assert calculate_exact_match("A", None) is False

def test_f1_exact_match():
    assert calculate_f1_score("A", "A") == 1.0
    assert calculate_f1_score("A", "B") == 0.0

def test_f1_set_based():
    # Simulate list inputs
    pred = ["A", "B", "C"]
    gt = ["B", "C", "D"]
    # Intersection: B, C (2)
    # Union: A, B, C, D (4)
    # Precision: 2/3
    # Recall: 2/3
    # F1: 2 * (2/3 * 2/3) / (4/3) = 2 * 4/9 / 4/3 = 8/9 * 3/4 = 24/36 = 2/3 = 0.666...
    f1 = calculate_f1_score(pred, gt)
    assert abs(f1 - 0.6666) < 0.001

def test_compute_row_metrics():
    pred = {'prediction': 'A', 'status': 'Success'}
    gt = {'label': 'A'}
    vlm = {'prediction': 'B'}
    lat = {'latency_ms': 100}
    
    row = compute_row_metrics("s1", pred, gt, vlm, lat)
    
    assert row['scene_id'] == "s1"
    assert row['symbolic_pred'] == 'A'
    assert row['vlm_pred'] == 'B'
    assert row['ground_truth'] == 'A'
    assert row['exact_match'] == 1
    assert row['f1'] == 1.0
    assert row['latency_ms'] == 100
    assert row['status'] == 'Success'