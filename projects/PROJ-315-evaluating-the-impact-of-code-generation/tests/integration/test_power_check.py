"""
Integration test for power insufficiency check (T012).

Verifies that the pipeline halts and raises an error if any classification group
(LLM vs Non-LLM) has fewer than 500 records, satisfying FR-008 (Power Analysis)
and FR-014 (Data Completeness/Power Check).
"""
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.config import set_global_seed
from code.data.preprocess import check_data_completeness, validate_dataset
from code.utils.logger import log_power_insufficiency

# Constants from tasks.md
MIN_GROUP_SIZE = 500
VALIDATION_ERROR_PATH = "docs/reports/error_report.json"

def setup_test_environment():
    """Create temporary directories for test artifacts."""
    temp_dir = tempfile.mkdtemp()
    docs_reports_dir = os.path.join(temp_dir, "docs", "reports")
    os.makedirs(docs_reports_dir, exist_ok=True)
    return temp_dir, docs_reports_dir

def cleanup_test_environment(temp_dir):
    """Remove temporary test directories."""
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def test_power_insufficiency_trigger():
    """
    Test that a dataset with < 500 items in one group triggers a ValueError.
    
    Scenario:
    1. Create a mock dataset with 600 LLM records and 400 Non-LLM records.
    2. Run the validation logic.
    3. Verify that a ValueError is raised.
    4. Verify that docs/reports/error_report.json is created with correct details.
    """
    temp_dir, reports_dir = setup_test_environment()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        set_global_seed(42)
        
        # Create mock data
        # LLM group: 600 rows (Passes)
        llm_data = pd.DataFrame({
            'pr_id': [f'pr_llm_{i}' for i in range(600)],
            'is_llm_generated': [True] * 600,
            'review_comments': [10] * 600
        })
        
        # Non-LLM group: 400 rows (Fails - < 500)
        non_llm_data = pd.DataFrame({
            'pr_id': [f'pr_non_{i}' for i in range(400)],
            'is_llm_generated': [False] * 400,
            'review_comments': [5] * 400
        })
        
        # Combine
        mock_df = pd.concat([llm_data, non_llm_data], ignore_index=True)
        
        # Mock the logger to avoid file write issues in temp dir if needed,
        # but we specifically want to test the file write for error_report.json
        # so we rely on the real logger behavior which writes to docs/reports/
        
        # Execute validation
        # We expect this to raise ValueError
        error_raised = False
        error_message = ""
        
        try:
            # The validate_dataset function calls check_data_completeness internally
            # and raises ValueError if thresholds aren't met.
            validate_dataset(mock_df, min_group_size=MIN_GROUP_SIZE)
        except ValueError as e:
            error_raised = True
            error_message = str(e)
        
        assert error_raised, "Expected ValueError to be raised for insufficient power, but none was raised."
        assert "power insufficiency" in error_message.lower() or "group size" in error_message.lower(), \
            f"Error message should mention power or group size. Got: {error_message}"
        
        # Verify error report file exists
        error_report_path = os.path.join(reports_dir, "error_report.json")
        assert os.path.exists(error_report_path), \
            f"Error report file {error_report_path} was not created."
        
        with open(error_report_path, 'r') as f:
            report_data = json.load(f)
        
        assert report_data.get('status') == 'failed', "Report status should be 'failed'."
        assert 'power_insufficiency' in report_data.get('reason', '').lower(), \
            f"Report reason should indicate power insufficiency. Got: {report_data.get('reason')}"
        assert report_data.get('details', {}).get('min_required') == MIN_GROUP_SIZE, \
            "Report should state the minimum required group size."
            
        # Check specific group counts in report
        details = report_data.get('details', {})
        assert details.get('llm_count') == 600, "LLM count mismatch in report."
        assert details.get('non_llm_count') == 400, "Non-LLM count mismatch in report."
        
        print("✓ Test passed: Power insufficiency correctly detected and reported.")
        
    finally:
        os.chdir(original_cwd)
        cleanup_test_environment(temp_dir)

def test_power_sufficiency_pass():
    """
    Test that a dataset with >= 500 items in both groups passes validation.
    """
    temp_dir, reports_dir = setup_test_environment()
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        set_global_seed(42)
        
        # Create mock data with sufficient size
        llm_data = pd.DataFrame({
            'pr_id': [f'pr_llm_{i}' for i in range(550)],
            'is_llm_generated': [True] * 550,
            'review_comments': [10] * 550
        })
        
        non_llm_data = pd.DataFrame({
            'pr_id': [f'pr_non_{i}' for i in range(550)],
            'is_llm_generated': [False] * 550,
            'review_comments': [5] * 550
        })
        
        mock_df = pd.concat([llm_data, non_llm_data], ignore_index=True)
        
        # Remove any existing error report from previous tests if in same dir
        error_report_path = os.path.join(reports_dir, "error_report.json")
        if os.path.exists(error_report_path):
            os.remove(error_report_path)
        
        # Execute validation - should NOT raise
        try:
            validate_dataset(mock_df, min_group_size=MIN_GROUP_SIZE)
            success = True
        except ValueError:
            success = False
        
        assert success, "Validation should pass when both groups have >= 500 items."
        
        # Verify NO error report was created
        assert not os.path.exists(error_report_path), \
            "Error report should not exist when validation passes."
            
        print("✓ Test passed: Sufficient power correctly validated.")
        
    finally:
        os.chdir(original_cwd)
        cleanup_test_environment(temp_dir)

if __name__ == "__main__":
    print("Running Power Insufficiency Integration Tests (T012)...")
    test_power_insufficiency_trigger()
    test_power_sufficiency_pass()
    print("All T012 tests completed successfully.")
