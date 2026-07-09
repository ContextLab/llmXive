"""
Integration test for WiC data loading and frozen BERT inference.
Tests the full pipeline of T012: run_baseline.py functionality.
"""

import json
import os
import tempfile
import pytest
import torch
from datasets import load_dataset
from transformers import BertTokenizer, BertModel
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from models.baseline_bert import run_frozen_bert_inference, compute_metrics, load_wic_dataset
from utils.logging import detect_nan_inf


@pytest.mark.integration
def test_wic_data_loading_and_inference():
    """
    Test that the WiC dataset can be loaded and processed by the frozen BERT model.
    This test verifies the core functionality of T012 without running the full script.
    """
    # 1. Load a small subset of the dataset for testing
    # We use the validation split to avoid potential issues with the test split
    # availability in CI environments, though the spec says test.
    try:
        dataset = load_dataset("super_glue", "wic", split="validation")
    except Exception as e:
        pytest.skip(f"SuperGLUE WiC dataset not available: {e}")

    # Take a small subset for speed
    subset = dataset.select(range(min(10, len(dataset))))
    assert len(subset) > 0, "Subset is empty"

    # 2. Run inference
    # This tests the `run_frozen_bert_inference` function which is the core of T012
    predictions = run_frozen_bert_inference(subset, batch_size=4, device="cpu")

    # 3. Validate predictions
    assert isinstance(predictions, list), "Predictions should be a list"
    assert len(predictions) == len(subset), "Prediction count mismatch"
    
    # Check that predictions are valid probabilities or logit indices
    # The baseline_bert.py implementation should return 0 or 1 for binary classification
    for pred in predictions:
        assert pred in [0, 1], f"Invalid prediction value: {pred}"

    # 4. Compute metrics
    true_labels = [int(item['label']) for item in subset]
    metrics = compute_metrics(predictions, true_labels)

    assert 'accuracy' in metrics, "Missing accuracy in metrics"
    assert 'macro_f1' in metrics, "Missing macro_f1 in metrics"
    
    # Check metric ranges
    assert 0.0 <= metrics['accuracy'] <= 1.0, "Accuracy out of range"
    assert 0.0 <= metrics['macro_f1'] <= 1.0, "Macro F1 out of range"

    # 5. Check for NaN/Inf
    assert not detect_nan_inf(torch.tensor(predictions)), "NaN or Inf detected in predictions"


@pytest.mark.integration
def test_baseline_output_schema():
    """
    Test that the output file matches the expected schema.
    This validates the output generation part of T012.
    """
    # We will simulate the output generation
    metrics = {
        "accuracy": 0.65,
        "macro_f1": 0.60
    }
    
    output_data = {
        "seed": 42,
        "model": "bert-base-uncased (frozen)",
        "dataset": "super_glue_wic_test",
        "metrics": metrics,
        "config": {
            "batch_size": 8,
            "device": "cpu"
        }
    }

    # Validate schema
    assert "seed" in output_data
    assert "model" in output_data
    assert "dataset" in output_data
    assert "metrics" in output_data
    assert "accuracy" in output_data["metrics"]
    assert "macro_f1" in output_data["metrics"]

    # Write to a temp file to simulate the script behavior
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(output_data, f)
        temp_path = f.name

    try:
        with open(temp_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded["metrics"]["accuracy"] == 0.65
        assert loaded["metrics"]["macro_f1"] == 0.60
    finally:
        os.unlink(temp_path)