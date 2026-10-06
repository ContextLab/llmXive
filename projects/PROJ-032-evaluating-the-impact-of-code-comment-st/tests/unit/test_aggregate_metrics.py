import os
import json
import csv
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to import the module under test.
# Since the project structure is 'code/', we need to ensure the path is correct.
# In a real test runner, the code/ directory should be in sys.path.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from aggregate_metrics import load_metric_file, aggregate_metrics, OUTPUT_FILE

def test_load_metric_file_exists():
    """Test loading an existing JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.json"
        data = {"key": "value", "number": 42}
        with open(test_file, 'w') as f:
            json.dump(data, f)
        
        result = load_metric_file(test_file)
        assert result == data

def test_load_metric_file_missing():
    """Test loading a missing JSON file returns empty dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "nonexistent.json"
        result = load_metric_file(test_file)
        assert result == {}

def test_aggregate_metrics_creates_csv():
    """Test that aggregate_metrics creates the output CSV with correct structure."""
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Mock the data paths
        comments_file = tmpdir_path / "comments.json"
        churn_file = tmpdir_path / "churn_metrics.json"
        quality_file = tmpdir_path / "quality_metrics.json"
        complexity_file = tmpdir_path / "complexity_metrics.json"
        output_file = tmpdir_path / "metrics.csv"
        
        # Prepare mock data
        comments_data = [
            {"repo_id": "repo1", "readability": 50.5, "sentiment": 0.8, "density": 0.25},
            {"repo_id": "repo2", "readability": 60.0, "sentiment": -0.1, "density": 0.30}
        ]
        churn_data = [
            {"repo_id": "repo1", "churn": 150.0},
            {"repo_id": "repo2", "churn": 200.5}
        ]
        quality_data = [
            {"repo_id": "repo1", "bug_fix_rate": 0.1},
            {"repo_id": "repo2", "bug_fix_rate": 0.2}
        ]
        complexity_data = [
            {"repo_id": "repo1", "complexity": 10.5},
            {"repo_id": "repo2", "complexity": 12.0}
        ]
        
        # Write mock data
        with open(comments_file, 'w') as f: json.dump(comments_data, f)
        with open(churn_file, 'w') as f: json.dump(churn_data, f)
        with open(quality_file, 'w') as f: json.dump(quality_data, f)
        with open(complexity_file, 'w') as f: json.dump(complexity_data, f)
        
        # Patch the file paths in the module
        with patch('aggregate_metrics.COMMENTS_FILE', comments_file), \
             patch('aggregate_metrics.CHURN_FILE', churn_file), \
             patch('aggregate_metrics.QUALITY_FILE', quality_file), \
             patch('aggregate_metrics.COMPLEXITY_FILE', complexity_file), \
             patch('aggregate_metrics.OUTPUT_FILE', output_file):
            
            # Run aggregation
            aggregate_metrics()
            
            # Verify output file exists
            assert output_file.exists(), f"Output file {output_file} was not created."
            
            # Verify content
            with open(output_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
                
                # Check headers
                expected_headers = ["repo_id", "readability", "sentiment", "density", "churn", "bug_fix_rate", "complexity"]
                assert all(h in reader.fieldnames for h in expected_headers), f"Missing headers. Got: {reader.fieldnames}"
                
                # Check values and precision
                repo1 = next(r for r in rows if r["repo_id"] == "repo1")
                assert float(repo1["readability"]) == 50.5
                assert float(repo1["sentiment"]) == 0.8
                assert float(repo1["density"]) == 0.25
                assert float(repo1["churn"]) == 150.0
                assert float(repo1["bug_fix_rate"]) == 0.1
                assert float(repo1["complexity"]) == 10.5

def test_aggregate_metrics_precision():
    """Test that numeric values are rounded to 2 decimal places."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        comments_file = tmpdir_path / "comments.json"
        churn_file = tmpdir_path / "churn_metrics.json"
        quality_file = tmpdir_path / "quality_metrics.json"
        complexity_file = tmpdir_path / "complexity_metrics.json"
        output_file = tmpdir_path / "metrics.csv"
        
        # Data with many decimal places
        comments_data = [{"repo_id": "repo1", "readability": 50.123456, "sentiment": 0.888888, "density": 0.255555}]
        churn_data = [{"repo_id": "repo1", "churn": 150.999999}]
        quality_data = [{"repo_id": "repo1", "bug_fix_rate": 0.111111}]
        complexity_data = [{"repo_id": "repo1", "complexity": 10.555555}]
        
        with open(comments_file, 'w') as f: json.dump(comments_data, f)
        with open(churn_file, 'w') as f: json.dump(churn_data, f)
        with open(quality_file, 'w') as f: json.dump(quality_data, f)
        with open(complexity_file, 'w') as f: json.dump(complexity_data, f)
        
        with patch('aggregate_metrics.COMMENTS_FILE', comments_file), \
             patch('aggregate_metrics.CHURN_FILE', churn_file), \
             patch('aggregate_metrics.QUALITY_FILE', quality_file), \
             patch('aggregate_metrics.COMPLEXITY_FILE', complexity_file), \
             patch('aggregate_metrics.OUTPUT_FILE', output_file):
            
            aggregate_metrics()
            
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                row = next(reader)
                
                # Check rounding
                assert float(row["readability"]) == 50.12
                assert float(row["sentiment"]) == 0.89
                assert float(row["density"]) == 0.26
                assert float(row["churn"]) == 151.0
                assert float(row["bug_fix_rate"]) == 0.11
                assert float(row["complexity"]) == 10.56