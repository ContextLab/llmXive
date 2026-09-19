"""
Integration tests for the smoke test script.
"""
import pytest
import os
import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.scripts.run_smoke_test import select_smoke_datasets, verify_outputs
from code.config import RESULTS_DIR

class TestSmokeTest:
    def test_select_smoke_datasets_count(self):
        """Verify that exactly 3 datasets are selected."""
        dataset_ids = select_smoke_datasets()
        assert len(dataset_ids) == 3, f"Expected 3 datasets, got {len(dataset_ids)}"
    
    def test_select_smoke_datasets_types(self):
        """Verify that selected dataset IDs are integers."""
        dataset_ids = select_smoke_datasets()
        for ds_id in dataset_ids:
            assert isinstance(ds_id, int), f"Dataset ID {ds_id} is not an integer"
    
    @pytest.mark.skipif(not RESULTS_DIR.exists(), reason="Results directory not created")
    def test_verify_outputs_structure(self):
        """Verify that output files have the expected structure (if they exist)."""
        # This test is skipped if the smoke test hasn't been run yet
        # In a real CI environment, this would be run after the smoke test
        required_files = [
            "raw_evaluations.csv",
            "stability_metrics.csv",
            "correlation_results.csv",
            "permutation_results.csv",
            "final_report.md"
        ]
        
        for file_name in required_files:
            file_path = RESULTS_DIR / file_name
            if file_path.exists():
                assert file_path.stat().st_size > 0, f"File {file_name} is empty"
            else:
                pytest.skip(f"File {file_name} does not exist yet")
