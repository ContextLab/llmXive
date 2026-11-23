import pytest
import pandas as pd
import numpy as np
from code.simulate import validate_design_adherence
from code.meta_analysis import validate_design_adherence as validate_meta

class TestBetweenSubjectsValidation:
    def test_valid_between_design(self):
        """Test that a valid between-subjects dataframe passes."""
        data = {
            "participant_id": ["sub_001", "sub_002", "sub_003"],
            "status_level": ["High", "Low", "High"],
            "observed_behavior": ["Risky", "Conservative", "Risky"],
            "risk_taking_score": [50.0, 55.0, 48.0]
        }
        df = pd.DataFrame(data)
        assert validate_design_adherence(df, "between") is True

    def test_invalid_between_design_duplicate_participants(self):
        """Test that a between-subjects dataframe with duplicate participants fails."""
        data = {
            "participant_id": ["sub_001", "sub_001", "sub_002"],
            "status_level": ["High", "Low", "High"],
            "observed_behavior": ["Risky", "Conservative", "Risky"],
            "risk_taking_score": [50.0, 55.0, 48.0]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError, match="Design Violation"):
            validate_design_adherence(df, "between")

class TestWithinSubjectsValidation:
    def test_valid_within_design(self):
        """Test that a valid within-subjects dataframe passes."""
        # 2 participants, 4 conditions each = 8 rows
        rows = []
        for pid in ["sub_001", "sub_002"]:
            for status in ["High", "Low"]:
                for behavior in ["Risky", "Conservative"]:
                    rows.append({
                        "participant_id": pid,
                        "status_level": status,
                        "observed_behavior": behavior,
                        "risk_taking_score": 50.0
                    })
        df = pd.DataFrame(rows)
        assert validate_design_adherence(df, "within") is True

    def test_invalid_within_design_missing_conditions(self):
        """Test that a within-subjects dataframe missing a condition fails."""
        # sub_001 missing (Low, Conservative)
        rows = [
            {"participant_id": "sub_001", "status_level": "High", "observed_behavior": "Risky", "risk_taking_score": 50.0},
            {"participant_id": "sub_001", "status_level": "High", "observed_behavior": "Conservative", "risk_taking_score": 50.0},
            {"participant_id": "sub_001", "status_level": "Low", "observed_behavior": "Risky", "risk_taking_score": 50.0},
            # Missing Low/Conservative for sub_001
            {"participant_id": "sub_002", "status_level": "High", "observed_behavior": "Risky", "risk_taking_score": 50.0},
            {"participant_id": "sub_002", "status_level": "High", "observed_behavior": "Conservative", "risk_taking_score": 50.0},
            {"participant_id": "sub_002", "status_level": "Low", "observed_behavior": "Risky", "risk_taking_score": 50.0},
            {"participant_id": "sub_002", "status_level": "Low", "observed_behavior": "Conservative", "risk_taking_score": 50.0},
        ]
        df = pd.DataFrame(rows)
        with pytest.raises(ValueError, match="Design Violation"):
            validate_design_adherence(df, "within")

    def test_invalid_within_design_wrong_count(self):
        """Test that a within-subjects dataframe with wrong row count fails."""
        rows = []
        for pid in ["sub_001"]:
            # Only 2 rows instead of 4
            for status in ["High", "Low"]:
                rows.append({
                    "participant_id": pid,
                    "status_level": status,
                    "observed_behavior": "Risky",
                    "risk_taking_score": 50.0
                })
        df = pd.DataFrame(rows)
        with pytest.raises(ValueError, match="Design Violation"):
            validate_design_adherence(df, "within")