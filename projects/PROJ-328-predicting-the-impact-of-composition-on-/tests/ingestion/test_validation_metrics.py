"""
Unit tests for T014a: validation_metrics.py
"""
import os
import sys
import csv
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# Setup paths to simulate project structure
test_dir = Path(__file__).parent
project_root = test_dir.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.validation_metrics import calculate_validation_metrics, save_metrics
from config import get_data_processed_dir

class TestValidationMetrics:
    def setup_method(self):
        """Create temporary directories and mock data files."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.temp_dir) / "raw"
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()

        # Mock config override (if needed, but we will pass paths directly or mock get_data_* if necessary)
        # For simplicity, we will test the logic functions directly with file paths passed or by mocking the config.
        # Since the functions use get_data_* which relies on global state, we will test the logic by creating files in temp dirs
        # and patching the config or passing arguments if the functions allowed it.
        # However, the current implementation relies on global config.
        # Let's test the logic by creating the files in the temp dir and mocking the config functions.
        
        # We will mock the config functions to point to our temp dirs.
        import ingestion.validation_metrics as vm_module
        from config import get_data_raw_dir, get_data_processed_dir
        
        # Save original functions
        self.orig_raw_dir = get_data_raw_dir
        self.orig_proc_dir = get_data_processed_dir
        
        # Patch
        vm_module.get_data_raw_dir = lambda: self.raw_dir
        vm_module.get_data_processed_dir = lambda: self.processed_dir

    def teardown_method(self):
        """Cleanup temporary directories."""
        shutil.rmtree(self.temp_dir)
        # Restore original functions if we had stored them in a way to restore
        # (In a real test, we'd use unittest.mock.patch)

    def test_calculate_metrics_with_composition_failures(self):
        """Test calculation when some records fail composition sum."""
        # Create raw file
        raw_csv = self.raw_dir / "literature_scraped.csv"
        with open(raw_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['element', 'percentage', 'hardness_hv', 'citation']) # Dummy header
            writer.writerow(['Sn', '60', '10', 'A'])
            writer.writerow(['Sn', '40', '10', 'B'])
            writer.writerow(['Sn', '90', '10', 'C'])
            # Total 3 records

        # Create excluded file with 1 composition failure
        exc_csv = self.processed_dir / "excluded_records.csv"
        with open(exc_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['alloy_id', 'reason', 'details'])
            writer.writerow(['alloy_3', 'COMPOSITION_SUM_LOW', 'sum=90'])

        # Calculate
        # We need to call the logic that reads these files.
        # The main() function calls count_raw_records() and calculate_validation_metrics().
        # Let's call the helper logic directly by patching the internal calls or just running main() if it's safe.
        # Since we patched get_data_* in the module, we can run the logic.
        
        from ingestion.validation_metrics import count_raw_records, calculate_validation_metrics, save_metrics
        
        total = count_raw_records()
        assert total == 3, f"Expected 3 raw records, got {total}"
        
        metrics = calculate_validation_metrics(total, 0)
        
        assert metrics['total_raw_records'] == 3
        assert metrics['failed_threshold_count'] == 1
        assert metrics['passed_threshold_count'] == 2
        assert metrics['pass_rate_percentage'] == pytest.approx(66.67, rel=0.1)

    def test_calculate_metrics_no_failures(self):
        """Test calculation when no records fail."""
        # Create raw file
        raw_csv = self.raw_dir / "literature_scraped.csv"
        with open(raw_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['element', 'percentage', 'hardness_hv', 'citation'])
            writer.writerow(['Sn', '99', '10', 'A'])
            writer.writerow(['Sn', '98', '10', 'B'])

        # Create empty excluded file
        exc_csv = self.processed_dir / "excluded_records.csv"
        with open(exc_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['alloy_id', 'reason', 'details'])

        from ingestion.validation_metrics import count_raw_records, calculate_validation_metrics
        
        total = count_raw_records()
        assert total == 2
        
        metrics = calculate_validation_metrics(total, 0)
        
        assert metrics['failed_threshold_count'] == 0
        assert metrics['passed_threshold_count'] == 2
        assert metrics['pass_rate_percentage'] == pytest.approx(100.0)

    def test_save_metrics(self):
        """Test saving metrics to YAML."""
        metrics = {
            "total_raw_records": 10,
            "passed_threshold_count": 8,
            "failed_threshold_count": 2,
            "pass_rate_percentage": 80.0
        }
        
        save_metrics(metrics)
        
        output_file = self.processed_dir / "validation_metrics.yaml"
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        assert loaded == metrics
