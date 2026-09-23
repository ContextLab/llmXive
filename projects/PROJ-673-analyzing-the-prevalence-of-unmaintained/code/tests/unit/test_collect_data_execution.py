import pytest
import json
import csv
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from src.cli.collect_data import calculate_and_export_metrics, export_to_csv

def test_export_to_csv_creates_file():
    """Verify that export_to_csv actually writes the file to disk."""
    test_data = [
        {
            "package": "test-pkg",
            "version": "1.0.0",
            "dependencies": [
                {
                    "name": "dep1",
                    "version": "2.0.0",
                    "last_commit_date": "2023-01-01",
                    "last_release_date": "2023-01-01",
                    "age_in_days": 365,
                    "vulnerability_count": 0,
                    "has_release_metadata": True
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.csv"
        export_to_csv(test_data, output_path)

        assert output_path.exists(), "CSV file was not created"
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['name'] == 'dep1'
            assert rows[0]['age_in_days'] == '365'

def test_calculate_metrics_includes_null_ratio():
    """Verify that metrics calculation includes the missing release ratio."""
    test_data = [
        {
            "package": "test-pkg",
            "version": "1.0.0",
            "dependencies": [
                {
                    "name": "dep1",
                    "version": "2.0.0",
                    "last_commit_date": "2023-01-01",
                    "last_release_date": None,
                    "age_in_days": None,
                    "vulnerability_count": 1,
                    "has_release_metadata": False
                },
                {
                    "name": "dep2",
                    "version": "3.0.0",
                    "last_commit_date": "2023-01-01",
                    "last_release_date": "2023-01-01",
                    "age_in_days": 100,
                    "vulnerability_count": 0,
                    "has_release_metadata": True
                }
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metrics.json"
        calculate_and_export_metrics(test_data, output_path)

        assert output_path.exists(), "Metrics file was not created"
        
        with open(output_path, 'r') as f:
            metrics = json.load(f)
            assert metrics["total_dependencies"] == 2
            assert metrics["missing_release_metadata_count"] == 1
            assert metrics["missing_release_metadata_ratio"] == 0.5