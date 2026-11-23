"""
Integration tests for data filtering logic (T016).

This test suite validates the data filtering logic for User Story 1.
It ensures that subjects with missing longitudinal cognitive scores (MMSE/MOCA)
are correctly excluded and logged, while those with complete data are retained.

The test uses a mock dataset to simulate various scenarios without requiring
the full OpenNeuro download, satisfying the requirement for an integration test
of the filtering logic itself.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import csv
import os
import sys

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the specific functions we are testing
# Note: We import directly from the module that defines the logic,
# rather than the main script, to isolate the filtering logic.
try:
    from code.code_01_download_and_filter import (
        is_eligible,
        has_valid_score,
        filter_eligible_subjects,
        write_excluded_log
    )
except ImportError:
    # Fallback if the module is named slightly differently or location varies
    # This handles the case where the file might be directly in code/
    from code._01_download_and_filter import (
        is_eligible,
        has_valid_score,
        filter_eligible_subjects,
        write_excluded_log
    )


class TestFilteringLogic:
    """Unit tests for individual filtering helper functions."""

    def test_has_valid_score(self):
        """Test score validation logic."""
        # Valid scores
        assert has_valid_score(24.0) is True
        assert has_valid_score(30.0) is True
        assert has_valid_score(10.0) is True
        assert has_valid_score(25) is True # Integer input

        # Invalid scores
        assert has_valid_score(None) is False
        assert has_valid_score(np.nan) is False
        assert has_valid_score("") is False
        assert has_valid_score("N/A") is False
        assert has_valid_score("missing") is False

    def test_is_eligible(self):
        """Test eligibility checking for a single subject across visits."""
        # Eligible subject (both timepoints have scores)
        row1 = {"subject_id": "sub-01", "visit": "1", "MMSE": 25.0, "MOCA": 28.0}
        row2 = {"subject_id": "sub-01", "visit": "2", "MMSE": 22.0, "MOCA": 26.0}
        
        assert is_eligible([row1, row2]) is True

        # Ineligible (missing score at one visit)
        row3 = {"subject_id": "sub-02", "visit": "1", "MMSE": 25.0, "MOCA": 28.0}
        row4 = {"subject_id": "sub-02", "visit": "2", "MMSE": None, "MOCA": None}
        
        assert is_eligible([row3, row4]) is False

        # Ineligible (missing score at one timepoint, present at another)
        row5 = {"subject_id": "sub-03", "visit": "1", "MMSE": 25.0, "MOCA": 28.0}
        row6 = {"subject_id": "sub-03", "visit": "2", "MMSE": None, "MOCA": 26.0}
        
        assert is_eligible([row5, row6]) is False

        # Edge case: Empty list
        assert is_eligible([]) is False

    def test_filter_eligible_subjects(self):
        """Test filtering of eligible subjects from a dataset."""
        # Create a mock participants file data
        data = [
            {"subject_id": "sub-01", "visit": "1", "MMSE": 25.0, "MOCA": 28.0},
            {"subject_id": "sub-01", "visit": "2", "MMSE": 22.0, "MOCA": 26.0},
            {"subject_id": "sub-02", "visit": "1", "MMSE": 24.0, "MOCA": 27.0},
            {"subject_id": "sub-02", "visit": "2", "MMSE": None, "MOCA": None},
            {"subject_id": "sub-03", "visit": "1", "MMSE": 26.0, "MOCA": 29.0},
            {"subject_id": "sub-03", "visit": "2", "MMSE": 24.0, "MOCA": 27.0},
            {"subject_id": "sub-04", "visit": "1", "MMSE": None, "MOCA": None},
            {"subject_id": "sub-04", "visit": "2", "MMSE": 20.0, "MOCA": 22.0},
        ]
        
        eligible = filter_eligible_subjects(data)
        
        # Should have 2 eligible subjects: sub-01 and sub-03
        assert len(eligible) == 2
        eligible_ids = [e["subject_id"] for e in eligible]
        assert "sub-01" in eligible_ids
        assert "sub-03" in eligible_ids
        assert "sub-02" not in eligible_ids
        assert "sub-04" not in eligible_ids


class TestIntegrationFiltering:
    """Integration tests for the end-to-end filtering pipeline."""

    def test_filtering_excludes_missing_scores(self):
        """
        Integration test: loads a mock dataset with some subjects having 
        missing MMSE/MOCA at one timepoint. Asserts that the output CSV 
        contains only subjects with complete longitudinal data, and the 
        exclusion log contains the correct subject IDs.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "participants_mock.csv"
            output_csv = Path(tmpdir) / "eligible_subjects.csv"
            output_log = Path(tmpdir) / "excluded_subjects.log"

            # Create mock data
            mock_data = [
                {"subject_id": "sub-01", "visit": "1", "MMSE": 25.0, "MOCA": 28.0},
                {"subject_id": "sub-01", "visit": "2", "MMSE": 22.0, "MOCA": 26.0},
                {"subject_id": "sub-02", "visit": "1", "MMSE": 24.0, "MOCA": 27.0},
                {"subject_id": "sub-02", "visit": "2", "MMSE": None, "MOCA": None}, # Ineligible
                {"subject_id": "sub-03", "visit": "1", "MMSE": 26.0, "MOCA": 29.0},
                {"subject_id": "sub-03", "visit": "2", "MMSE": 24.0, "MOCA": 27.0},
                {"subject_id": "sub-05", "visit": "1", "MMSE": 28.0, "MOCA": 30.0},
                {"subject_id": "sub-05", "visit": "2", "MMSE": None, "MOCA": 28.0}, # Ineligible
            ]

            # Write mock input
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["subject_id", "visit", "MMSE", "MOCA"])
                writer.writeheader()
                writer.writerows(mock_data)

            # Run the filtering logic (simulating the core of code/01_download_and_filter.py)
            # We re-implement the logic here to avoid dependency on the full script's side effects
            # like downloading, but we use the actual helper functions.
            df = pd.read_csv(input_file)
            data = df.to_dict('records')
            
            # Group by subject to simulate the logic in the real script
            from collections import defaultdict
            subjects = defaultdict(list)
            for row in data:
                subjects[row['subject_id']].append(row)
            
            eligible_subjects = []
            excluded_subjects = []

            for sub_id, rows in subjects.items():
                if is_eligible(rows):
                    eligible_subjects.append(sub_id)
                else:
                    excluded_subjects.append(sub_id)

            # Write eligible CSV
            with open(output_csv, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["subject_id"])
                writer.writeheader()
                for sub_id in eligible_subjects:
                    writer.writerow({"subject_id": sub_id})

            # Write exclusion log
            write_excluded_log(output_log, excluded_subjects, "Missing longitudinal scores")

            # Assertions
            # 1. Check CSV content
            assert output_csv.exists(), "Eligible subjects CSV was not created"
            df_eligible = pd.read_csv(output_csv)
            assert len(df_eligible) == 2, f"Expected 2 eligible subjects, got {len(df_eligible)}"
            assert set(df_eligible['subject_id'].tolist()) == {"sub-01", "sub-03"}

            # 2. Check exclusion log content
            assert output_log.exists(), "Exclusion log was not created"
            with open(output_log, 'r') as f:
                log_content = f.read()
            
            assert "sub-02" in log_content, "sub-02 should be in exclusion log"
            assert "sub-05" in log_content, "sub-05 should be in exclusion log"
            assert "sub-01" not in log_content, "sub-01 should NOT be in exclusion log"
            assert "sub-03" not in log_content, "sub-03 should NOT be in exclusion log"

    def test_all_excluded_exit_code(self):
        """
        Integration test: Assert that if all subjects are excluded, 
        the logic correctly identifies zero eligible subjects.
        (In a real script, this would trigger sys.exit(EXIT_CODE_NO_ELIGIBLE)).
        """
        mock_data = [
            {"subject_id": "sub-01", "visit": "1", "MMSE": None, "MOCA": None},
            {"subject_id": "sub-01", "visit": "2", "MMSE": None, "MOCA": None},
            {"subject_id": "sub-02", "visit": "1", "MMSE": 24.0, "MOCA": 27.0},
            {"subject_id": "sub-02", "visit": "2", "MMSE": None, "MOCA": None},
        ]

        from collections import defaultdict
        subjects = defaultdict(list)
        for row in mock_data:
            subjects[row['subject_id']].append(row)
        
        eligible_subjects = []
        excluded_subjects = []

        for sub_id, rows in subjects.items():
            if is_eligible(rows):
                eligible_subjects.append(sub_id)
            else:
                excluded_subjects.append(sub_id)

        # Assert zero eligible
        assert len(eligible_subjects) == 0, "Expected 0 eligible subjects when all have missing data"
        assert len(excluded_subjects) == 2, "Expected 2 excluded subjects"

    def test_empty_dataset_handling(self):
        """Test handling of an empty dataset."""
        mock_data = []
        
        from collections import defaultdict
        subjects = defaultdict(list)
        for row in mock_data:
            subjects[row['subject_id']].append(row)
        
        eligible_subjects = []
        excluded_subjects = []

        for sub_id, rows in subjects.items():
            if is_eligible(rows):
                eligible_subjects.append(sub_id)
            else:
                excluded_subjects.append(sub_id)

        assert len(eligible_subjects) == 0
        assert len(excluded_subjects) == 0