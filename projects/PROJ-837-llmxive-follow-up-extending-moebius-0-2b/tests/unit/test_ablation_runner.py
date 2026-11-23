"""
Unit tests for the ablation runner (T033a).
"""
import os
import sys
import json
import tempfile
import csv
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from eval.ablation_runner import load_test_samples, run_inference_batch, run_ablation_comparison

def test_load_test_samples():
    """Test that test samples are generated correctly."""
    samples = load_test_samples(5)
    assert len(samples) == 5
    assert "image_id" in samples[0]
    assert "image" in samples[0]
    assert "mask" in samples[0]
    assert "complexity_score" in samples[0]

def test_run_ablation_comparison_writes_csv():
    """Test that the runner writes the CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_latency.csv")
        samples = load_test_samples(5)
        
        # Run the comparison
        run_ablation_comparison(samples, output_path, mode="CI")
        
        # Verify file exists
        assert os.path.exists(output_path)
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5
            assert "latency_ms" in rows[0]
            assert "complexity_score" in rows[0]