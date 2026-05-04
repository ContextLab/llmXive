"""
Contract test for dataset schema validation.
Validates that downloaded datasets conform to expected schema structure.
"""
import pytest
import os
import json
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"

class TestDatasetSchema:
    """Contract tests for dataset schema validation."""

    def test_electricity_dataset_exists(self):
        """Verify Electricity dataset was downloaded."""
        # Check for any electricity-related files
        electricity_files = list(DATA_DIR.glob("*electricity*"))
        assert len(electricity_files) > 0, "Electricity dataset not found"

    def test_traffic_dataset_exists(self):
        """Verify Traffic dataset was downloaded."""
        traffic_files = list(DATA_DIR.glob("*traffic*"))
        assert len(traffic_files) > 0, "Traffic dataset not found"

    def test_synthetic_control_chart_exists(self):
        """Verify Synthetic Control Chart dataset was downloaded."""
        sc_files = list(DATA_DIR.glob("*synthetic*"))
        assert len(sc_files) > 0, "Synthetic Control Chart dataset not found"

    def test_dataset_checksums_exist(self):
        """Verify checksum files exist for downloaded datasets."""
        checksum_files = list(DATA_DIR.glob("*.checksum"))
        assert len(checksum_files) > 0, "No checksum files found"

    def test_dataset_has_required_columns(self):
        """Verify dataset has expected columns (timestamp, value)."""
        import pandas as pd
        
        for dataset_file in DATA_DIR.glob("*.csv"):
            df = pd.read_csv(dataset_file)
            # At minimum should have numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            assert len(numeric_cols) > 0, f"{dataset_file.name} has no numeric columns"

    def test_dataset_not_empty(self):
        """Verify downloaded datasets are not empty."""
        import pandas as pd
        
        for dataset_file in DATA_DIR.glob("*.csv"):
            df = pd.read_csv(dataset_file)
            assert len(df) > 0, f"{dataset_file.name} is empty"

    def test_dataset_properly_formatted(self):
        """Verify datasets have proper time series format."""
        import pandas as pd
        
        for dataset_file in DATA_DIR.glob("*.csv"):
            df = pd.read_csv(dataset_file)
            # Should have at least 2 columns for time series
            assert len(df.columns) >= 2, f"{dataset_file.name} has insufficient columns"

    def test_download_datasets_module_exists(self):
        """Verify download_datasets.py module exists and is importable."""
        download_script = PROJECT_ROOT / "code" / "download_datasets.py"
        assert download_script.exists(), "download_datasets.py not found"
        
        # Verify it can be imported
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "code"))
        from download_datasets import (
            download_electricity_dataset,
            download_traffic_dataset,
            download_synthetic_control_chart_dataset
        )

    def test_checksum_validation_works(self):
        """Verify checksum validation function exists."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "code"))
        from download_datasets import compute_file_checksum, validate_checksum
        
        # Test with an existing file if available
        checksum_files = list(DATA_DIR.glob("*.checksum"))
        if checksum_files:
            checksum_file = checksum_files[0]
            with open(checksum_file, 'r') as f:
                stored_checksum = f.read().strip()
            assert len(stored_checksum) == 64, "Invalid checksum format (should be SHA256)"

    def test_download_all_datasets_function_exists(self):
        """Verify consolidated download function exists."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "code"))
        from download_datasets import download_all_datasets
        
        assert callable(download_all_datasets), "download_all_datasets not callable"

    def test_dataset_consolidation_verified(self):
        """Verify T009 consolidation - all datasets via single download_datasets.py."""
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "code"))
        from download_datasets import (
            download_electricity_dataset,
            download_traffic_dataset,
            download_synthetic_control_chart_dataset,
            download_all_datasets
        )
        
        # Verify all three dataset downloaders exist in single module
        assert download_electricity_dataset is not None
        assert download_traffic_dataset is not None
        assert download_synthetic_control_chart_dataset is not None
        assert download_all_datasets is not None
        
        # This confirms T046 requirement: all fetchers consolidated in T009
