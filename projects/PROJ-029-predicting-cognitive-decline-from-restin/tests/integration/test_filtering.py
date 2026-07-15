"""
Integration tests for data filtering logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import csv

from code_01_download_and_filter import (
    is_eligible,
    has_valid_score,
    filter_eligible_subjects
)


class TestFilteringLogic:
    def test_has_valid_score(self):
        """Test score validation logic."""
        # Valid scores
        assert has_valid_score(24.0) is True
        assert has_valid_score(30.0) is True
        assert has_valid_score(10.0) is True
        
        # Invalid scores
        assert has_valid_score(None) is False
        assert has_valid_score(np.nan) is False
        assert has_valid_score("") is False
        assert has_valid_score("N/A") is False

    def test_is_eligible(self):
        """Test eligibility checking."""
        # Eligible subject (both timepoints have scores)
        row1 = {"subject_id": "sub-01", "visit": "1", "MMSE": 25.0, "MOCA": 28.0}
        row2 = {"subject_id": "sub-01", "visit": "2", "MMSE": 22.0, "MOCA": 26.0}
        
        assert is_eligible([row1, row2]) is True

        # Ineligible (missing score at one visit)
        row3 = {"subject_id": "sub-02", "visit": "1", "MMSE": 25.0, "MOCA": 28.0}
        row4 = {"subject_id": "sub-02", "visit": "2", "MMSE": None, "MOCA": None}
        
        assert is_eligible([row3, row4]) is False

    def test_filter_eligible_subjects(self):
        """Test filtering of eligible subjects."""
        # Create a mock participants file
        data = [
            {"subject_id": "sub-01", "visit": "1", "MMSE": 25.0, "MOCA": 28.0},
            {"subject_id": "sub-01", "visit": "2", "MMSE": 22.0, "MOCA": 26.0},
            {"subject_id": "sub-02", "visit": "1", "MMSE": 24.0, "MOCA": 27.0},
            {"subject_id": "sub-02", "visit": "2", "MMSE": None, "MOCA": None},
            {"subject_id": "sub-03", "visit": "1", "MMSE": 26.0, "MOCA": 29.0},
            {"subject_id": "sub-03", "visit": "2", "MMSE": 24.0, "MOCA": 27.0},
        ]
        
        eligible = filter_eligible_subjects(data)
        
        assert len(eligible) == 2
        assert "sub-01" in [e["subject_id"] for e in eligible]
        assert "sub-03" in [e["subject_id"] for e in eligible]
        assert "sub-02" not in [e["subject_id"] for e in eligible]

class TestIntegrationFiltering:
    def test_end_to_end_filtering(self):
        """Test end-to-end filtering with a temporary file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id", "visit", "MMSE", "MOCA"])
            writer.writeheader()
            writer.writerow({"subject_id": "sub-01", "visit": "1", "MMSE": 25.0, "MOCA": 28.0})
            writer.writerow({"subject_id": "sub-01", "visit": "2", "MMSE": 22.0, "MOCA": 26.0})
            writer.writerow({"subject_id": "sub-02", "visit": "1", "MMSE": 24.0, "MOCA": 27.0})
            writer.writerow({"subject_id": "sub-02", "visit": "2", "MMSE": None, "MOCA": None})
            temp_path = f.name
        
        try:
            df = pd.read_csv(temp_path)
            data = df.to_dict('records')
            eligible = filter_eligible_subjects(data)
            
            assert len(eligible) == 1
            assert eligible[0]["subject_id"] == "sub-01"
        finally:
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)