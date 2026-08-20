import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import subprocess
import sys

def test_integration_script_execution():
    """Test that the validation script runs correctly via CLI."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_path = Path(tmpdir) / "test_dataset.parquet"
        report_path = Path(tmpdir) / "test_report.json"
        
        # Create a valid dataset
        df = pd.DataFrame({
            'source': ['imagenet-1k'] * 500 + ['laion-400m'] * 500,
            'embedding': [[0.1] * 768 for _ in range(1000)],
            'routing_label': ['exp1'] * 500 + ['exp2'] * 500
        })
        df.to_parquet(dataset_path)
        
        # Run the script
        script_path = Path("code/00_validate_sources.py")
        if not script_path.exists():
            pytest.skip("Validation script not found")
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--dataset_path", str(dataset_path), "--report_path", str(report_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert report_path.exists()
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report['is_valid'] is True
        assert report['total_rows'] == 1000
        assert report['source_counts']['imagenet-1k'] == 500
        assert report['source_counts']['laion-400m'] == 500

def test_integration_script_fails_missing_source():
    """Test that the validation script fails correctly when source is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_path = Path(tmpdir) / "test_dataset.parquet"
        report_path = Path(tmpdir) / "test_report.json"
        
        # Create a dataset with only one source
        df = pd.DataFrame({
            'source': ['imagenet-1k'] * 1000,
            'embedding': [[0.1] * 768 for _ in range(1000)],
            'routing_label': ['exp1'] * 1000
        })
        df.to_parquet(dataset_path)
        
        # Run the script
        script_path = Path("code/00_validate_sources.py")
        if not script_path.exists():
            pytest.skip("Validation script not found")
        
        result = subprocess.run(
            [sys.executable, str(script_path), "--dataset_path", str(dataset_path), "--report_path", str(report_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 1, "Script should fail when source is missing"
        assert "Missing required sources" in result.stdout
        
        if report_path.exists():
            with open(report_path, 'r') as f:
                report = json.load(f)
            assert report['is_valid'] is False
