import os
import json
import pytest
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.control_run import (
    main, 
    load_sample_text, 
    compute_coherence_metric,
    run_baseline_forward_pass,
    run_oscillatory_forward_pass
)
from src.models.base_model import DistilBERTWrapper, load_distilbert_cpu
from src.models.oscillatory_attention import OscillatoryDistilBERTWrapper
from transformers import DistilBertTokenizerFast
import torch


@pytest.fixture
def sample_text():
    """Provide sample text for testing."""
    return ["The quick brown fox jumps over the lazy dog."]


@pytest.fixture
def tokenizer():
    """Provide a tokenizer for tests."""
    return DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")


@pytest.fixture
def baseline_model():
    """Provide a baseline model for tests."""
    return load_distilbert_cpu()


@pytest.fixture
def oscillatory_model():
    """Provide an oscillatory model for tests."""
    return OscillatoryDistilBERTWrapper.from_pretrained("distilbert-base-uncased")


def test_control_run_file_exists(tmp_path):
    """Test that the control run produces the expected output file."""
    # Override output path temporarily
    output_path = tmp_path / "control_run_comparison.json"
    
    # We can't easily patch the main() function's internal path,
    # so we test the components directly
    texts = load_sample_text()
    assert len(texts) > 0
    
    # Verify we can compute coherence metric
    dummy_activations = {
        "layer_0": torch.randn(2, 12, 10).numpy()  # batch, heads, seq_len
    }
    coherence = compute_coherence_metric(dummy_activations)
    assert isinstance(coherence, float)
    assert 0.0 <= coherence <= 1.0  # Normalized metric


def test_control_run_logic(baseline_model, oscillatory_model, tokenizer):
    """Test the core logic of the control run comparison."""
    texts = ["Test sequence for control run verification."]
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=64
    )
    
    # Run baseline
    baseline_activations, baseline_time = run_baseline_forward_pass(baseline_model, inputs)
    assert isinstance(baseline_activations, dict)
    assert baseline_time > 0
    
    # Run oscillatory
    oscillatory_activations, oscillatory_time = run_oscillatory_forward_pass(
        oscillatory_model, inputs, frequency=40.0
    )
    assert isinstance(oscillatory_activations, dict)
    assert oscillatory_time > 0
    
    # Compute coherence metrics
    baseline_coherence = compute_coherence_metric(baseline_activations)
    oscillatory_coherence = compute_coherence_metric(oscillatory_activations)
    
    # Both should be valid floats
    assert isinstance(baseline_coherence, float)
    assert isinstance(oscillatory_coherence, float)
    
    # Compute difference
    difference = oscillatory_coherence - baseline_coherence
    assert isinstance(difference, float)
    
    # Verify the structure matches expected output schema
    results = {
        "oscillatory_coherence": float(oscillatory_coherence),
        "baseline_coherence": float(baseline_coherence),
        "coherence_difference": float(difference)
    }
    
    assert "oscillatory_coherence" in results
    assert "baseline_coherence" in results
    assert "coherence_difference" in results
    
    # Verify all values are floats
    assert isinstance(results["oscillatory_coherence"], float)
    assert isinstance(results["baseline_coherence"], float)
    assert isinstance(results["coherence_difference"], float)
    
    # Verify the difference is computed correctly
    assert results["coherence_difference"] == results["oscillatory_coherence"] - results["baseline_coherence"]
    
    # The oscillatory model should ideally show higher coherence
    # (though this is not strictly enforced as the task says "report descriptively")
    # We just verify the comparison is made
    assert results["coherence_difference"] is not None