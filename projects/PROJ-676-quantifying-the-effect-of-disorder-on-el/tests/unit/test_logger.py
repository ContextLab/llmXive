"""
Unit tests for NumericalLogger (T017a).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from code.logger import NumericalLogger

def test_log_residual_writes_json_lines():
    """Test that log_residual writes a valid JSON line to the file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "residuals.json")
        logger = NumericalLogger(output_path)
        
        logger.log_residual(
            norm=1e-7,
            flag=True,
            task="eigh",
            L=100,
            W=1.0,
            realization_index=0,
            seed=42
        )
        
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            line = f.readline()
            entry = json.loads(line)
            
        assert entry["task"] == "eigh"
        assert entry["residual_norm"] == 1e-7
        assert entry["converged"] is True
        assert entry["L"] == 100
        assert entry["W"] == 1.0
        assert entry["realization_index"] == 0
        assert entry["seed"] == 42

def test_log_convergence_writes_json_lines():
    """Test that log_convergence writes a valid JSON line to the file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "residuals.json")
        logger = NumericalLogger(output_path)
        
        metric = {
            "iterations": 10,
            "history": [1.0, 0.5, 0.1],
            "converged": True
        }
        logger.log_convergence(metric)
        
        assert os.path.exists(output_path)
        with open(output_path, "r") as f:
            line = f.readline()
            entry = json.loads(line)
            
        assert entry["type"] == "convergence_metric"
        assert entry["metric"]["iterations"] == 10
        assert entry["metric"]["converged"] is True

def test_ensure_directory_creates_path():
    """Test that _ensure_directory creates parent directories if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_path = os.path.join(tmpdir, "deep", "nested", "residuals.json")
        logger = NumericalLogger(nested_path)
        assert os.path.exists(os.path.dirname(nested_path))
