"""
Unit tests for T019: tune_threshold.py
"""
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from tune_threshold import (
    load_pilot_traces,
    load_pilot_labels,
    align_traces_and_labels,
    compute_agreement,
    tune_threshold
)

@pytest.fixture
def sample_traces():
    return [
        {
            "task_id": "task_001",
            "trace_text": "The object is red and circular.",
            "constraint": "red circular object",
            "segments": [{"text": "The object is red and circular."}]
        },
        {
            "task_id": "task_002",
            "trace_text": "A blue square.",
            "constraint": "blue square",
            "segments": [{"text": "A blue square."}]
        }
    ]

@pytest.fixture
def sample_labels():
    return [
        {"task_id": "task_001", "constraint_mention": "yes", "task_outcome": "correct"},
        {"task_id": "task_002", "constraint_mention": "yes", "task_outcome": "incorrect"}
    ]

@pytest.fixture
def mock_model():
    model = MagicMock()
    # Mock embeddings to return predictable results
    # Task 001: High similarity (should match)
    # Task 002: Low similarity (should not match at high threshold)
    model.encode.return_value = np.array([
        [1.0, 0.0, 0.0],  # Trace 1
        [0.9, 0.1, 0.0],  # Constraint 1 -> High sim
        [0.0, 1.0, 0.0],  # Trace 2
        [0.1, 0.9, 0.0]   # Constraint 2 -> Low sim
    ])
    return model

def test_load_pilot_traces_valid(sample_traces, tmp_path):
    file_path = tmp_path / "traces.jsonl"
    with open(file_path, 'w') as f:
        for trace in sample_traces:
            f.write(json.dumps(trace) + '\n')
    
    loaded = load_pilot_traces(file_path)
    assert len(loaded) == 2
    assert loaded[0]['task_id'] == 'task_001'

def test_load_pilot_traces_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_pilot_traces(tmp_path / "nonexistent.jsonl")

def test_load_pilot_labels_valid(sample_labels, tmp_path):
    file_path = tmp_path / "labels.jsonl"
    with open(file_path, 'w') as f:
        for label in sample_labels:
            f.write(json.dumps(label) + '\n')
    
    loaded = load_pilot_labels(file_path)
    assert len(loaded) == 2
    assert loaded[0]['constraint_mention'] == 'yes'

def test_load_pilot_labels_invalid_schema(tmp_path):
    file_path = tmp_path / "labels.jsonl"
    with open(file_path, 'w') as f:
        f.write(json.dumps({"task_id": "bad"}) + '\n')  # Missing constraint_mention
    
    with pytest.raises(ValueError):
        load_pilot_labels(file_path)

def test_align_traces_and_labels(sample_traces, sample_labels):
    aligned = align_traces_and_labels(sample_traces, sample_labels)
    assert len(aligned) == 2
    # Check alignment
    assert aligned[0][0]['task_id'] == 'task_001'
    assert aligned[0][1]['task_id'] == 'task_001'

def test_align_traces_and_labels_missing_label(sample_traces):
    labels = [{"task_id": "task_999", "constraint_mention": "yes"}]
    aligned = align_traces_and_labels(sample_traces, labels)
    assert len(aligned) == 0  # No matches

@patch('tune_threshold.encode_texts')
@patch('tune_threshold.cosine_similarity')
def test_compute_agreement_high_similarity(mock_sim, mock_encode, sample_traces, sample_labels, mock_model):
    mock_encode.return_value = np.array([[1.0, 0.0], [0.99, 0.01]])
    mock_sim.return_value = 0.99  # High similarity
    
    trace, label = sample_traces[0], sample_labels[0]
    auto_mention, matches = compute_agreement(trace, label, threshold=0.5, model=mock_model)
    
    assert auto_mention is True
    assert matches is True

@patch('tune_threshold.encode_texts')
@patch('tune_threshold.cosine_similarity')
def test_compute_agreement_low_similarity(mock_sim, mock_encode, sample_traces, sample_labels, mock_model):
    mock_encode.return_value = np.array([[1.0, 0.0], [0.1, 0.9]])
    mock_sim.return_value = 0.1  # Low similarity
    
    trace, label = sample_traces[0], sample_labels[0]
    auto_mention, matches = compute_agreement(trace, label, threshold=0.5, model=mock_model)
    
    assert auto_mention is False
    assert matches is False  # Ground truth is "yes", automated is "no" -> mismatch

@patch('tune_threshold.encode_texts')
@patch('tune_threshold.cosine_similarity')
def test_tune_threshold(mock_sim, mock_encode, sample_traces, sample_labels, mock_model):
    # Setup mock to return specific similarities for deterministic testing
    # We want to verify the logic finds the max agreement
    
    # Simulate: 
    # Threshold 0.5 -> High sim passes, Low sim fails. 
    # If Ground Truth for high is Yes and low is No -> Perfect agreement.
    
    def side_effect_sim(a, b):
        # Return fixed values for testing
        return 0.95 if np.array_equal(a, b) else 0.2
    
    mock_encode.return_value = np.array([[1.0, 0.0], [0.95, 0.05], [0.0, 1.0], [0.05, 0.95]])
    mock_sim.side_effect = side_effect_sim
    
    aligned = align_traces_and_labels(sample_traces, sample_labels)
    best_thresh, metrics = tune_threshold(aligned, mock_model, thresholds=[0.5, 0.9])
    
    assert best_thresh is not None
    assert 'agreement_rate' in metrics
    assert metrics['total'] == 2
