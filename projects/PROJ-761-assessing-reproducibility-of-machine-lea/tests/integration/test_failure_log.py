import json
import os
import tempfile
import pytest
from pathlib import Path
from code.failure_logger import compile_failure_summary, write_failure_report, load_existing_failure_log

def test_compile_failure_summary_from_results():
    """Test that compile_failure_summary correctly extracts failures from repro results."""
    # Create a temporary directory for test artifacts
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = os.path.join(tmpdir, "repro_results.json")
        output_path = os.path.join(tmpdir, "failure_log.json")
        
        # Mock repro results with various flags
        mock_results = [
            {
                "doi": "10.1038/s41586-021-03000-1",
                "flags": ["model_substituted"],
                "mae": 0.5,
                "r2": 0.8
            },
            {
                "doi": "10.1038/s41586-021-03000-2",
                "flags": ["data_unavailable", "covariate_missing"],
                "mae": 0.6,
                "r2": 0.75
            },
            {
                "doi": "10.1038/s41586-021-03000-3",
                "flags": [],  # No failure
                "mae": 0.4,
                "r2": 0.9
            },
            {
                "doi": "10.1038/s41586-021-03000-4",
                "flags": ["missing_seed"],
                "mae": 0.55,
                "r2": 0.82
            }
        ]
        
        with open(results_path, 'w') as f:
            json.dump(mock_results, f)
        
        # Compile failures
        failures = compile_failure_summary(results_path)
        
        # Verify structure and content
        assert isinstance(failures, list)
        assert len(failures) == 3  # 3 papers had failures
        
        # Check specific failure modes
        failure_modes = {f['failure_mode'] for f in failures}
        assert "Model Substitution" in failure_modes
        assert "Data Unavailable" in failure_modes
        assert "Missing Covariates" in failure_modes
        assert "Missing Seed" in failure_modes
        
        # Verify DOI mapping
        dois = {f['paper_doi'] for f in failures}
        assert "10.1038/s41586-021-03000-1" in dois
        assert "10.1038/s41586-021-03000-2" in dois
        assert "10.1038/s41586-021-03000-4" in dois
        assert "10.1038/s41586-021-03000-3" not in dois  # No failure

def test_write_failure_report():
    """Test that write_failure_report correctly writes to a JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "failure_log.json")
        
        mock_failures = [
            {
                "paper_doi": "10.1038/s41586-021-03000-1",
                "failure_mode": "Model Substitution",
                "details": "Model exceeded 1M parameter limit."
            }
        ]
        
        write_failure_report(mock_failures, output_path)
        
        # Verify file exists and content matches
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            content = json.load(f)
        
        assert content == mock_failures

def test_load_existing_failure_log():
    """Test loading an existing failure log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "existing_log.json")
        
        mock_log = [
            {
                "paper_doi": "10.1038/s41586-021-03000-5",
                "failure_mode": "Other",
                "details": "Some other error."
            }
        ]
        
        with open(log_path, 'w') as f:
            json.dump(mock_log, f)
        
        loaded_log = load_existing_failure_log(log_path)
        assert loaded_log == mock_log
        
        # Test non-existent file
        non_existent = load_existing_failure_log(os.path.join(tmpdir, "non_existent.json"))
        assert non_existent == []

def test_compile_failure_summary_merges_existing():
    """Test that compile_failure_summary merges existing failures with new ones."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_path = os.path.join(tmpdir, "repro_results.json")
        existing_log_path = os.path.join(tmpdir, "existing_log.json")
        
        mock_results = [
            {
                "doi": "10.1038/s41586-021-03000-1",
                "flags": ["model_substituted"]
            }
        ]
        
        mock_existing = [
            {
                "paper_doi": "10.1038/s41586-021-03000-5",
                "failure_mode": "Other",
                "details": "Pre-existing failure."
            }
        ]
        
        with open(results_path, 'w') as f:
            json.dump(mock_results, f)
        
        with open(existing_log_path, 'w') as f:
            json.dump(mock_existing, f)
        
        failures = compile_failure_summary(results_path, existing_log_path)
        
        assert len(failures) == 2
        dois = {f['paper_doi'] for f in failures}
        assert "10.1038/s41586-021-03000-1" in dois
        assert "10.1038/s41586-021-03000-5" in dois