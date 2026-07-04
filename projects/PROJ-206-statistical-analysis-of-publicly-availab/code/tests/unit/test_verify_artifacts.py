"""
Unit tests for T033: verify_artifacts.py
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
import yaml
import pandas as pd
import numpy as np
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.verify_artifacts import (
    compute_file_hash, 
    check_checksums, 
    detect_fabrication,
    load_state_file
)

class TestComputeFileHash:
    def test_compute_hash_valid_file(self, tmp_path):
        file_path = tmp_path / "test.txt"
        content = "Hello World"
        file_path.write_text(content)
        
        expected_hash = hashlib.sha256(content.encode()).hexdigest()
        actual_hash = compute_file_hash(file_path)
        
        assert actual_hash == expected_hash

    def test_compute_hash_nonexistent(self, tmp_path):
        file_path = tmp_path / "nonexistent.txt"
        assert compute_file_hash(file_path) is None

class TestCheckChecksums:
    def test_checksums_valid(self, tmp_path):
        # Create a mock state dict
        content = "test data"
        file_path = tmp_path / "data.csv"
        file_path.write_text(content)
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        
        state = {
            "artifacts": {
                "test_artifact": {
                    "path": str(file_path.relative_to(tmp_path.parent)),
                    "sha256": file_hash
                }
            }
        }
        
        # Mock project_root to be tmp_path.parent
        import code.verify_artifacts as mod
        original_root = mod.project_root
        mod.project_root = tmp_path.parent
        
        try:
            ok, errors = check_checksums(state)
            assert ok is True
            assert len(errors) == 0
        finally:
            mod.project_root = original_root

    def test_checksums_mismatch(self, tmp_path):
        file_path = tmp_path / "data.csv"
        file_path.write_text("real data")
        
        state = {
            "artifacts": {
                "test_artifact": {
                    "path": str(file_path.relative_to(tmp_path.parent)),
                    "sha256": "wrong_hash"
                }
            }
        }
        
        import code.verify_artifacts as mod
        original_root = mod.project_root
        mod.project_root = tmp_path.parent
        
        try:
            ok, errors = check_checksums(state)
            assert ok is False
            assert len(errors) == 1
        finally:
            mod.project_root = original_root

    def test_checksums_missing_file(self, tmp_path):
        state = {
            "artifacts": {
                "test_artifact": {
                    "path": "nonexistent.csv",
                    "sha256": "some_hash"
                }
            }
        }
        
        import code.verify_artifacts as mod
        original_root = mod.project_root
        mod.project_root = tmp_path.parent
        
        try:
            ok, errors = check_checksums(state)
            assert ok is False
            assert len(errors) == 1
        finally:
            mod.project_root = original_root

class TestDetectFabrication:
    def test_constant_column_suspicion(self, tmp_path):
        # Create a CSV with a constant column (suspicious)
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "vote_share": [50.0, 50.0, 50.0], # Constant
            "sample_size": [100, 200, 300]
        })
        file_path = tmp_path / "fake_data.csv"
        df.to_csv(file_path, index=False)
        
        is_clean, warnings = detect_fabrication(file_path)
        assert is_clean is False
        assert any("vote_share" in w for w in warnings)
        
    def test_realistic_data_clean(self, tmp_path):
        # Create a CSV with realistic variation
        np.random.seed(42)
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "vote_share": np.random.normal(50, 2, 10),
            "sample_size": np.random.randint(800, 1200, 10)
        })
        file_path = tmp_path / "real_data.csv"
        df.to_csv(file_path, index=False)
        
        is_clean, warnings = detect_fabrication(file_path)
        # Should be clean or at least not flag constant values
        # We don't assert is_clean=True because other heuristics might trigger,
        # but we assert no constant warnings.
        constant_warnings = [w for w in warnings if "constant" in w.lower()]
        assert len(constant_warnings) == 0

    def test_missing_file(self, tmp_path):
        file_path = tmp_path / "missing.csv"
        is_clean, warnings = detect_fabrication(file_path)
        assert is_clean is True # Function returns True if file missing, just warns
        assert len(warnings) == 1
        assert "not found" in warnings[0].lower()

class TestLoadStateFile:
    def test_load_valid_yaml(self, tmp_path):
        file_path = tmp_path / "state.yaml"
        data = {"key": "value", "nested": {"a": 1}}
        with open(file_path, 'w') as f:
            yaml.dump(data, f)
        
        result = load_state_file(file_path)
        assert result == data

    def test_load_nonexistent(self, tmp_path):
        result = load_state_file(tmp_path / "nonexistent.yaml")
        assert result == {}