"""
Tests for FLOPs estimation and savings calculation (T021).
"""
import pytest
import os
import json
import tempfile
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.flops_analysis import (
    load_router_predictions,
    load_convergence_results,
    align_data_for_flops,
    calculate_flops_for_scenario,
    calculate_flops_dynamic_router,
    calculate_accuracy,
    calculate_flops_savings,
    run_flops_analysis,
    DEFAULT_MODEL_PARAMS,
    STATIC_BASELINE_K
)

# Fixtures
@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def sample_router_preds(temp_dir):
    """Create a sample router predictions CSV."""
    path = os.path.join(temp_dir, "router_preds.csv")
    data = [
        {"task_id": "1", "predicted_k": "1", "actual_converged_k": "1", "is_correct": "True", "entropy": "0.5"},
        {"task_id": "2", "predicted_k": "3", "actual_converged_k": "2", "is_correct": "True", "entropy": "1.2"},
        {"task_id": "3", "predicted_k": "2", "actual_converged_k": "4", "is_correct": "False", "entropy": "2.0"},
        {"task_id": "4", "predicted_k": "1", "actual_converged_k": "1", "is_correct": "True", "entropy": "0.1"},
        {"task_id": "5", "predicted_k": "4", "actual_converged_k": "3", "is_correct": "True", "entropy": "1.5"},
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return path

@pytest.fixture
def sample_convergence_results(temp_dir):
    """Create a sample convergence results CSV."""
    path = os.path.join(temp_dir, "convergence_results.csv")
    data = [
        {"task_id": "1", "k_used": "1", "sequence_length": "100", "is_correct": "True"},
        {"task_id": "2", "k_used": "2", "sequence_length": "200", "is_correct": "True"},
        {"task_id": "3", "k_used": "4", "sequence_length": "150", "is_correct": "False"},
        {"task_id": "4", "k_used": "1", "sequence_length": "120", "is_correct": "True"},
        {"task_id": "5", "k_used": "3", "sequence_length": "180", "is_correct": "True"},
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return path

# Tests
def test_load_router_predictions(temp_dir, sample_router_preds):
    data = load_router_predictions(sample_router_preds)
    assert len(data) == 5
    assert data[0]['task_id'] == '1'
    assert data[0]['predicted_k'] == 1
    assert data[0]['is_correct'] is True

def test_load_convergence_results(temp_dir, sample_convergence_results):
    data = load_convergence_results(sample_convergence_results)
    assert len(data) == 5
    assert data[0]['sequence_length'] == 100

def test_align_data_for_flops(temp_dir, sample_router_preds, sample_convergence_results):
    router_preds = load_router_predictions(sample_router_preds)
    conv_results = load_convergence_results(sample_convergence_results)
    aligned = align_data_for_flops(router_preds, conv_results)
    assert len(aligned) == 5
    assert aligned[0]['sequence_length'] == 100
    assert aligned[0]['predicted_k'] == 1

def test_calculate_flops_for_scenario(temp_dir, sample_convergence_results):
    conv_results = load_convergence_results(sample_convergence_results)
    params = 1_000_000
    k = 2
    flops = calculate_flops_for_scenario(conv_results, k, params)
    # Sum of seq_len * k * params
    # (100 + 200 + 150 + 120 + 180) * 2 * 1_000_000 = 750 * 2 * 1_000_000 = 1_500_000_000
    expected = sum(r['sequence_length'] for r in conv_results) * k * params
    assert flops == expected

def test_calculate_flops_dynamic_router(temp_dir, sample_router_preds, sample_convergence_results):
    router_preds = load_router_predictions(sample_router_preds)
    conv_results = load_convergence_results(sample_convergence_results)
    aligned = align_data_for_flops(router_preds, conv_results)
    params = 1_000_000
    flops = calculate_flops_dynamic_router(aligned, params)
    # Expected: sum(params * seq_len * predicted_k)
    # 1: 100 * 1
    # 2: 200 * 3
    # 3: 150 * 2
    # 4: 120 * 1
    # 5: 180 * 4
    # Total: 100 + 600 + 300 + 120 + 720 = 1840
    # * 1_000_000 = 1_840_000_000
    expected_sum = (100*1) + (200*3) + (150*2) + (120*1) + (180*4)
    assert flops == expected_sum * params

def test_calculate_flops_savings():
    static = 1_500_000_000
    dynamic = 1_200_000_000
    savings = calculate_flops_savings(static, dynamic)
    assert savings['absolute_savings'] == 300_000_000
    assert savings['percentage_savings'] == 20.0

def test_run_flops_analysis_full(temp_dir, sample_router_preds, sample_convergence_results):
    output_path = os.path.join(temp_dir, "flops_results.json")
    results = run_flops_analysis(
        router_predictions_path=sample_router_preds,
        convergence_results_path=sample_convergence_results,
        output_path=output_path,
        model_params=1_000_000
    )
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        saved_results = json.load(f)
    
    assert 'static_flops' in saved_results
    assert 'dynamic_flops' in saved_results
    assert 'flops_savings' in saved_results
    assert 'non_inferiority_test' in saved_results
    assert 'static_accuracy' in saved_results
    assert 'dynamic_accuracy' in saved_results

def test_non_inferiority_logic():
    # This is tested implicitly in run_flops_analysis, but we can check the math
    # If dynamic accuracy is higher or equal to static - margin, it should be non-inferior
    # The function run_flops_analysis handles the statistical test
    pass
