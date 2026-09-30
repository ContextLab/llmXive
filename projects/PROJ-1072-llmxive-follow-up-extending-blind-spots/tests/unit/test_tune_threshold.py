"""
Unit tests for T019: tune_threshold.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from tune_threshold import (
    load_pilot_traces,
    load_pilot_labels,
    align_traces_and_labels,
    compute_agreement,
    tune_threshold,
    save_results
)


@pytest.fixture
def sample_traces():
    return [
        {
            "task_id": "task_1",
            "constraint": "Find the object that is red",
            "cot_trace": "I need to find the red object."
        },
        {
            "task_id": "task_2",
            "constraint": "Sort the items by size",
            "cot_trace": "The items are sorted."
        }
    ]


@pytest.fixture
def sample_labels():
    return [
        {"task_id": "task_1", "constraint_mention": 1},
        {"task_id": "task_2", "constraint_mention": 0}
    ]


@pytest.fixture
def mock_model():
    model = MagicMock()
    # Return embeddings that result in high similarity for task_1, low for task_2
    # Task 1: "Find the object that is red" vs "I need to find the red object" -> High
    # Task 2: "Sort the items by size" vs "The items are sorted" -> Low
    model.encode.side_effect = lambda texts, **kwargs: np.array([
        [1.0, 0.0] if "red" in texts[0] else [0.0, 1.0], # Simplified mock
        [1.0, 0.0] if "red" in texts[1] else [0.0, 1.0]
    ])
    return model


def test_load_pilot_traces(tmp_path, sample_traces):
    file_path = tmp_path / "traces.jsonl"
    with open(file_path, "w") as f:
        for t in sample_traces:
            f.write(json.dumps(t) + "\n")
    
    result = load_pilot_traces(file_path)
    assert len(result) == 2
    assert result[0]["task_id"] == "task_1"


def test_load_pilot_labels_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_pilot_labels(tmp_path / "nonexistent.jsonl")


def test_align_traces_and_labels(sample_traces, sample_labels):
    aligned = align_traces_and_labels(sample_traces, sample_labels)
    assert len(aligned) == 2
    # Check order matches traces
    assert aligned[0][0]["task_id"] == "task_1"
    assert aligned[0][1]["constraint_mention"] == 1


def test_compute_agreement_high_threshold(mock_model, sample_traces, sample_labels):
    aligned = align_traces_and_labels(sample_traces, sample_labels)
    # High threshold (0.9) -> Only task_1 matches (high sim), task_2 doesn't (low sim)
    # Task 1: Human=1, Auto=True -> Agree
    # Task 2: Human=0, Auto=False -> Agree
    agreements, total, rate = compute_agreement(0.9, aligned, mock_model)
    assert total == 2
    assert agreements == 2
    assert rate == 1.0


def test_compute_agreement_low_threshold(mock_model, sample_traces, sample_labels):
    aligned = align_traces_and_labels(sample_traces, sample_labels)
    # Low threshold (0.1) -> Both match (sim > 0.1)
    # Task 1: Human=1, Auto=True -> Agree
    # Task 2: Human=0, Auto=True -> Disagree
    agreements, total, rate = compute_agreement(0.1, aligned, mock_model)
    assert total == 2
    assert agreements == 1
    assert rate == 0.5


def test_tune_threshold(mock_model, sample_traces, sample_labels):
    aligned = align_traces_and_labels(sample_traces, sample_labels)
    best_th, best_ag, history = tune_threshold(aligned, mock_model)
    
    assert 0.0 <= best_th <= 1.0
    assert len(history) > 0
    # With mock data, we expect high agreement at some point
    assert best_ag > 0.0


def test_save_results(tmp_path, mock_model, sample_traces, sample_labels):
    aligned = align_traces_and_labels(sample_traces, sample_labels)
    best_th, best_ag, history = tune_threshold(aligned, mock_model)
    output_path = tmp_path / "results.json"
    
    save_results(best_th, best_ag, history, output_path)
    
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    
    assert "best_threshold" in data
    assert "best_agreement_rate" in data
    assert "results_history" in data
    assert data["best_threshold"] == best_th
    assert data["best_agreement_rate"] == best_ag
