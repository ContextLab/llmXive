import json
import os
import tempfile
import time
import pytest
from unittest.mock import patch, mock_open

# We need to import the module under test. 
# Since the module uses relative imports for utils, we need to ensure the path is correct.
# Assuming tests are run from the project root or code is in the path.
# We will mock the file system interactions.

# Import the functions we want to test
# We need to handle the import path. The artifact is in code/utils/budget_report.py
# In the test environment, we assume 'code' is in sys.path or we import relative to root.
# Let's assume the test is run with PYTHONPATH set to include the project root.
try:
    from utils.budget_report import (
        load_start_time_marker,
        measure_total_runtime,
        load_budget_limit,
        write_report,
        run_budget_report
    )
except ImportError:
    # Fallback for direct execution context if needed, though standard is project root
    import sys
    sys.path.insert(0, 'code')
    from utils.budget_report import (
        load_start_time_marker,
        measure_total_runtime,
        load_budget_limit,
        write_report,
        run_budget_report
    )

class TestBudgetReport:
    def test_load_start_time_marker_found(self, tmp_path):
        marker_file = tmp_path / "pipeline_start_time.json"
        marker_file.write_text(json.dumps({"start_timestamp": 1000.0}))
        
        with patch('utils.budget_report.START_TIME_MARKER_FILE', str(marker_file)):
            result = load_start_time_marker()
            assert result == 1000.0

    def test_load_start_time_marker_not_found(self, tmp_path):
        non_existent = tmp_path / "non_existent.json"
        
        with patch('utils.budget_report.START_TIME_MARKER_FILE', str(non_existent)):
            result = load_start_time_marker()
            assert result is None

    def test_measure_total_runtime(self):
        start = time.time() - 10
        runtime = measure_total_runtime(start)
        assert 9 <= runtime <= 11  # Allow small variance

    def test_load_budget_limit_found(self, tmp_path):
        config_file = tmp_path / "power_config.yaml"
        config_content = """
        effect_size: 0.5
        max_runtime_hours: 2.0
        """
        config_file.write_text(config_content)
        
        with patch('utils.budget_report.BUDGET_LIMIT_FILE', str(config_file)):
            result = load_budget_limit()
            assert result == 2.0 * 3600.0

    def test_load_budget_limit_not_found(self, tmp_path):
        non_existent = tmp_path / "non_existent.yaml"
        
        with patch('utils.budget_report.BUDGET_LIMIT_FILE', str(non_existent)):
            result = load_budget_limit()
            assert result is None

    def test_write_report(self, tmp_path):
        output_file = tmp_path / "report.json"
        total_runtime = 100.0
        budget_limit = 200.0
        
        write_report(total_runtime, budget_limit, str(output_file))
        
        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        
        assert data["total_runtime_seconds"] == total_runtime
        assert data["budget_limit_seconds"] == budget_limit
        assert data["status"] == "PASS"

    def test_write_report_fail_status(self, tmp_path):
        output_file = tmp_path / "report_fail.json"
        total_runtime = 300.0
        budget_limit = 200.0
        
        write_report(total_runtime, budget_limit, str(output_file))
        
        with open(output_file) as f:
            data = json.load(f)
        
        assert data["status"] == "FAIL"