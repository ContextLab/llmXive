"""
Tests for T024e: Metadata Aggregation & Subset Selection
"""
import os
import sys
import json
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pipelines.aggregate_metadata_subset import (
    load_csv_data,
    save_csv_data,
    aggregate_and_select_subset
)

class TestAggregateMetadataSubset:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_input_csv(self, temp_dir):
        """Create a sample input CSV file."""
        input_path = Path(temp_dir) / "input.csv"
        data = [
            {"dataset_id": "dataset_z", "cardinality": "100", "missingness": "0.1", "sparsity": "0.5", "variance": "0.8"},
            {"dataset_id": "dataset_a", "cardinality": "50", "missingness": "0.0", "sparsity": "0.2", "variance": "0.9"},
            {"dataset_id": "dataset_m", "cardinality": "200", "missingness": "0.2", "sparsity": "0.6", "variance": "0.7"},
        ]
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return str(input_path)

    def test_load_csv_data(self, sample_input_csv):
        """Test loading CSV data."""
        data = load_csv_data(sample_input_csv)
        assert len(data) == 3
        assert data[0]['dataset_id'] == 'dataset_z'

    def test_aggregate_and_select_subset_sorts_and_flags(self, temp_dir):
        """Test that data is sorted alphabetically and shortfall is flagged correctly."""
        input_path = Path(temp_dir) / "input.csv"
        output_path = Path(temp_dir) / "output.csv"
        report_path = Path(temp_dir) / "report.json"
        
        # Create input with fewer than 10 datasets to trigger shortfall
        data = [
            {"dataset_id": "z", "cardinality": "1", "missingness": "0", "sparsity": "0", "variance": "1"},
            {"dataset_id": "a", "cardinality": "1", "missingness": "0", "sparsity": "0", "variance": "1"},
        ]
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        aggregate_and_select_subset(str(input_path), str(output_path), str(report_path))

        # Check output CSV
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        # Check sorting: a should be before z
        assert rows[0]['dataset_id'] == 'a'
        assert rows[1]['dataset_id'] == 'z'
        # Check selected flag
        assert rows[0]['selected'] == 'true'
        assert rows[1]['selected'] == 'true'

        # Check report
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        assert report['total_datasets'] == 2
        assert report['selected_datasets'] == 2
        assert report['shortfall_flag'] == True
        assert "below recommended minimum" in report['shortfall_reason']
        assert report['datasets'] == ['a', 'z']

    def test_aggregate_and_select_subset_no_shortfall(self, temp_dir):
        """Test that shortfall is not flagged when enough datasets exist."""
        input_path = Path(temp_dir) / "input.csv"
        output_path = Path(temp_dir) / "output.csv"
        report_path = Path(temp_dir) / "report.json"
        
        # Create 15 datasets
        data = []
        for i in range(15):
            data.append({
                "dataset_id": f"dataset_{i:02d}",
                "cardinality": "100",
                "missingness": "0.1",
                "sparsity": "0.5",
                "variance": "0.8"
            })
        
        # Shuffle to ensure sorting works
        import random
        random.seed(42)
        random.shuffle(data)

        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        aggregate_and_select_subset(str(input_path), str(output_path), str(report_path))

        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        assert report['total_datasets'] == 15
        assert report['shortfall_flag'] == False
        # Check sorting
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        ids = [r['dataset_id'] for r in rows]
        assert ids == sorted(ids)
