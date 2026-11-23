"""
Unit tests for the Final Consistency Check (T055) logic.
These tests verify that the pattern matching and artifact verification logic works correctly.
"""
import pytest
import os
import tempfile
from pathlib import Path
from code.final_consistency_check import (
    scan_codebase_for_synthetic_patterns,
    verify_artifacts_exist,
    FORBIDDEN_PATTERNS
)

def test_scan_codebase_for_synthetic_patterns_detects_fake():
    """Test that the scanner detects a file containing 'generate_synthetic'."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        code_dir = tmpdir / "code"
        code_dir.mkdir()
        
        # Create a file with forbidden pattern
        bad_file = code_dir / "bad_script.py"
        bad_file.write_text("def generate_synthetic_data():\n    return [1, 2, 3]\n")
        
        # Create a clean file
        clean_file = code_dir / "clean_script.py"
        clean_file.write_text("def clean_function():\n    return 42\n")
        
        violations = scan_codebase_for_synthetic_patterns(tmpdir)
        
        assert len(violations) == 1
        assert "bad_script.py" in violations[0][0]
        assert "generate_synthetic" in violations[0][2]

def test_scan_codebase_for_synthetic_patterns_ignores_tests():
    """Test that the scanner ignores files in test directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        test_dir = tmpdir / "tests"
        test_dir.mkdir()
        
        # Create a file with forbidden pattern in tests dir
        test_file = test_dir / "test_mock_data.py"
        test_file.write_text("def mock_data():\n    return [1, 2, 3]\n")
        
        violations = scan_codebase_for_synthetic_patterns(tmpdir)
        
        # Should be empty because we skip 'test' in path
        assert len(violations) == 0

def test_verify_artifacts_exist_detects_missing():
    """Test that artifact verification detects missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        processed_dir = tmpdir / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create one expected file
        existing = processed_dir / "existing.csv"
        existing.touch()
        
        # Define expected artifacts
        expected = {
            "data/processed/existing.csv": "T001",
            "data/processed/missing.csv": "T002"
        }
        
        missing = verify_artifacts_exist(tmpdir, expected)
        
        assert len(missing) == 1
        assert "missing.csv" in missing[0][0]

def test_forbidden_patterns_compiled():
    """Test that the forbidden patterns list is not empty and compiles."""
    assert len(FORBIDDEN_PATTERNS) > 0
    for pattern in FORBIDDEN_PATTERNS:
        try:
            import re
            re.compile(pattern, re.IGNORECASE)
        except re.error:
            pytest.fail(f"Invalid regex pattern: {pattern}")