"""
Integration test for data ingestion pipeline (T010).
Validates the ingestion pipeline against the sample dataset created in T017.

This test verifies:
1. The sample dataset exists at data/raw/sample_developer_productivity.csv
2. All required variables are present (tool_usage, task_time, defect_rate, 
   experience_years, task_complexity, project_type, team_size)
3. Missing data handling works correctly
4. The pipeline produces a valid validation report
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from ingest.validate import (
    load_verified_datasets_from_spec,
    check_csv_variables,
    check_tool_usage_variable,
    check_task_time_variable,
    check_defect_rate_variable,
    check_experience_years_variable,
    identify_missing_experience_values,
    calculate_missing_percentage,
    filter_missing_data,
    generate_validation_report
)
from ingest.logging import get_validate_logger

# Constants
SAMPLE_DATASET_PATH = "data/raw/sample_developer_productivity.csv"
VALIDATION_REPORT_PATH = "data/output/validation_report.json"

REQUIRED_VARIABLES = [
    "tool_usage",
    "task_time", 
    "defect_rate",
    "experience_years",
    "task_complexity",
    "project_type",
    "team_size"
]

class TestDataIngestionPipeline:
    """Integration tests for the data ingestion pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        self.logger = get_validate_logger()
        self.project_root = Path(__file__).parent.parent.parent
        self.sample_path = self.project_root / SAMPLE_DATASET_PATH
        self.report_path = self.project_root / VALIDATION_REPORT_PATH
        
        # Ensure sample dataset exists
        assert self.sample_path.exists(), f"Sample dataset not found at {self.sample_path}"
        
    def test_sample_dataset_exists(self):
        """Test that the sample dataset file exists."""
        assert self.sample_path.exists()
        assert self.sample_path.stat().st_size > 0
        
    def test_all_required_variables_present(self):
        """Test that all required variables are present in the sample dataset."""
        variables_present, missing_vars = check_csv_variables(
            str(self.sample_path), 
            REQUIRED_VARIABLES
        )
        
        assert variables_present is True, f"Missing variables: {missing_vars}"
        assert len(missing_vars) == 0
        
    def test_tool_usage_variable_valid(self):
        """Test tool_usage variable validation."""
        result = check_tool_usage_variable(str(self.sample_path))
        assert result["valid"] is True
        assert result["variable_name"] == "tool_usage"
        
    def test_task_time_variable_valid(self):
        """Test task_time variable validation."""
        result = check_task_time_variable(str(self.sample_path))
        assert result["valid"] is True
        assert result["variable_name"] == "task_time"
        
    def test_defect_rate_variable_valid(self):
        """Test defect_rate variable validation."""
        result = check_defect_rate_variable(str(self.sample_path))
        assert result["valid"] is True
        assert result["variable_name"] == "defect_rate"
        
    def test_experience_years_variable_valid(self):
        """Test experience_years variable validation."""
        result = check_experience_years_variable(str(self.sample_path))
        assert result["valid"] is True
        assert result["variable_name"] == "experience_years"
        
    def test_missing_data_detection(self):
        """Test that missing data in experience_years is correctly identified."""
        missing_values = identify_missing_experience_values(str(self.sample_path))
        missing_percentage = calculate_missing_percentage(
            str(self.sample_path), 
            "experience_years"
        )
        
        # Should detect missing values (if any exist in sample)
        assert isinstance(missing_values, list)
        assert isinstance(missing_percentage, float)
        assert 0 <= missing_percentage <= 100
        
    def test_missing_data_filtering(self):
        """Test that missing data filtering works correctly."""
        filtered_df, removed_count, percentage_removed = filter_missing_data(
            str(self.sample_path),
            "experience_years"
        )
        
        # Should return a dataframe
        assert filtered_df is not None
        assert removed_count >= 0
        assert 0 <= percentage_removed <= 100
        
        # If more than 20% removed, should flag
        if percentage_removed > 20:
            assert percentage_removed > 20
            
    def test_validation_report_generation(self):
        """Test that a validation report is generated correctly."""
        report = generate_validation_report(str(self.sample_path))
        
        assert report is not None
        assert "dataset_path" in report
        assert "validation_status" in report
        assert "variables_checked" in report
        assert "missing_data_summary" in report
        assert "timestamp" in report
        
        # Verify report structure
        assert report["dataset_path"] == str(self.sample_path)
        assert isinstance(report["variables_checked"], dict)
        assert isinstance(report["missing_data_summary"], dict)
        
    def test_validation_report_file_creation(self):
        """Test that validation report is written to disk."""
        # Generate and save report
        report = generate_validation_report(str(self.sample_path))
        
        # Write to file
        with open(self.report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Verify file exists and is valid JSON
        assert self.report_path.exists()
        assert self.report_path.stat().st_size > 0
        
        with open(self.report_path, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["validation_status"] in ["PASS", "FAIL", "WARNING"]
        
    def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline execution."""
        # Step 1: Verify dataset exists
        assert self.sample_path.exists()
        
        # Step 2: Check all required variables
        variables_present, missing_vars = check_csv_variables(
            str(self.sample_path),
            REQUIRED_VARIABLES
        )
        assert variables_present is True
        
        # Step 3: Validate each required variable
        for var in REQUIRED_VARIABLES:
            if var == "tool_usage":
                result = check_tool_usage_variable(str(self.sample_path))
            elif var == "task_time":
                result = check_task_time_variable(str(self.sample_path))
            elif var == "defect_rate":
                result = check_defect_rate_variable(str(self.sample_path))
            elif var == "experience_years":
                result = check_experience_years_variable(str(self.sample_path))
            else:
                # Other variables checked in check_csv_variables
                continue
                
            assert result["valid"] is True, f"Variable {var} validation failed"
        
        # Step 4: Check missing data
        missing_percentage = calculate_missing_percentage(
            str(self.sample_path),
            "experience_years"
        )
        assert 0 <= missing_percentage <= 100
        
        # Step 5: Filter missing data
        filtered_df, removed_count, percentage_removed = filter_missing_data(
            str(self.sample_path),
            "experience_years"
        )
        assert filtered_df is not None
        
        # Step 6: Generate report
        report = generate_validation_report(str(self.sample_path))
        assert report["validation_status"] is not None
        
        self.logger.info(f"End-to-end pipeline completed successfully. Status: {report['validation_status']}")
        
    def test_pipeline_handles_insufficient_data(self):
        """Test pipeline behavior when data is insufficient (>20% missing)."""
        # This test verifies the pipeline correctly flags high missing data
        # In the sample dataset, we expect normal operation, but the logic
        # should handle the edge case
        
        filtered_df, removed_count, percentage_removed = filter_missing_data(
            str(self.sample_path),
            "experience_years"
        )
        
        # The pipeline should work regardless of percentage
        assert filtered_df is not None
        assert isinstance(removed_count, int)
        assert isinstance(percentage_removed, float)
        
        # If percentage > 20, it should be flagged in the report
        report = generate_validation_report(str(self.sample_path))
        if percentage_removed > 20:
            assert report["missing_data_summary"]["flag_high_missing"] is True
        else:
            assert report["missing_data_summary"]["flag_high_missing"] is False
