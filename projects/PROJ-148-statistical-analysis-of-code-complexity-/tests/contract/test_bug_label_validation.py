"""
Contract test for bug-label reliability validation script.

This test verifies that the `validate_bug_labels` function in
`code/data/validate_bug_labels.py` correctly computes precision
against a provided ground truth and enforces the minimum precision
threshold (>= 85%) as required by the project specification.
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from data.validate_bug_labels import validate_bug_labels


class TestBugLabelValidation:
    """
    Contract tests for bug label validation logic.
    """

    def test_precision_above_threshold(self):
        """
        Verify that validation passes (precision >= 0.85) when the
        predicted labels match the ground truth with high accuracy.
        """
        # Create a synthetic dataset with high precision
        # 90% correct, 10% incorrect -> Precision = 0.90
        data = {
            "predicted_bug": [1, 1, 1, 1, 1, 1, 1, 1, 1, 0] * 10,
            "actual_bug":    [1, 1, 1, 1, 1, 1, 1, 1, 1, 0] * 9 + [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            "file_path": [f"file_{i}.java" for i in range(100)],
            "commit_hash": [f"hash_{i}" for i in range(100)]
        }
        # Adjust to ensure 90 predicted positives, 81 true positives
        # Let's construct explicitly:
        # 90 rows where predicted=1. Of these, 81 are actual=1 (TP), 9 are actual=0 (FP).
        # 10 rows where predicted=0.
        rows = []
        for i in range(81):
            rows.append({"predicted_bug": 1, "actual_bug": 1, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        for i in range(81, 90):
            rows.append({"predicted_bug": 1, "actual_bug": 0, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        for i in range(90, 100):
            rows.append({"predicted_bug": 0, "actual_bug": 0, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        
        df = pd.DataFrame(rows)

        result = validate_bug_labels(df, precision_threshold=0.85)

        assert result["passed"] is True, f"Expected pass, got precision: {result.get('precision')}"
        assert result["precision"] >= 0.85

    def test_precision_below_threshold_fails(self):
        """
        Verify that validation fails (precision < 0.85) when accuracy is low.
        """
        # 50% precision: 50 predicted positives, 25 true positives
        rows = []
        for i in range(25):
            rows.append({"predicted_bug": 1, "actual_bug": 1, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        for i in range(25, 50):
            rows.append({"predicted_bug": 1, "actual_bug": 0, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        for i in range(50, 100):
            rows.append({"predicted_bug": 0, "actual_bug": 0, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        
        df = pd.DataFrame(rows)

        result = validate_bug_labels(df, precision_threshold=0.85)

        assert result["passed"] is False
        assert result["precision"] < 0.85
        assert result["precision"] == 0.50

    def test_empty_predicted_positives(self):
        """
        Verify behavior when there are no predicted bug fixes (precision undefined or 0).
        """
        df = pd.DataFrame({
            "predicted_bug": [0] * 100,
            "actual_bug": [1] * 100,
            "file_path": [f"f{i}.java" for i in range(100)],
            "commit_hash": [f"h{i}" for i in range(100)]
        })

        result = validate_bug_labels(df, precision_threshold=0.85)

        # If no positives predicted, precision is technically undefined or 0 depending on convention.
        # The function should handle this gracefully and fail the threshold.
        assert result["passed"] is False

    def test_invalid_column_names(self):
        """
        Verify that the function raises an error or returns a failure if required columns are missing.
        """
        df = pd.DataFrame({
            "wrong_column_name": [1, 0, 1],
            "another_column": [1, 0, 1]
        })

        with pytest.raises(KeyError):
            validate_bug_labels(df, precision_threshold=0.85)

    def test_integration_with_realistic_distribution(self):
        """
        Test with a distribution that mimics a realistic bug-fix scenario
        (imbalanced classes).
        """
        # 1000 samples, 100 actual bugs.
        # Predicted 110 bugs: 90 true positives, 20 false positives.
        # Precision = 90 / 110 = ~0.818 -> Should fail 0.85 threshold.
        rows = []
        # 90 TP
        for i in range(90):
            rows.append({"predicted_bug": 1, "actual_bug": 1, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        # 20 FP
        for i in range(90, 110):
            rows.append({"predicted_bug": 1, "actual_bug": 0, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        # 10 FN (actual bug, predicted 0)
        for i in range(110, 120):
            rows.append({"predicted_bug": 0, "actual_bug": 1, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        # 880 TN
        for i in range(120, 1000):
            rows.append({"predicted_bug": 0, "actual_bug": 0, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        
        df = pd.DataFrame(rows)

        result = validate_bug_labels(df, precision_threshold=0.85)

        expected_precision = 90 / 110
        assert abs(result["precision"] - expected_precision) < 1e-6
        assert result["passed"] is False

    def test_exact_threshold_boundary(self):
        """
        Verify that exactly 85% precision passes the threshold.
        """
        # 100 predicted positives, 85 true positives -> 0.85
        rows = []
        for i in range(85):
            rows.append({"predicted_bug": 1, "actual_bug": 1, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        for i in range(85, 100):
            rows.append({"predicted_bug": 1, "actual_bug": 0, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        for i in range(100, 200):
            rows.append({"predicted_bug": 0, "actual_bug": 0, "file_path": f"f{i}.java", "commit_hash": f"h{i}"})
        
        df = pd.DataFrame(rows)

        result = validate_bug_labels(df, precision_threshold=0.85)

        assert result["passed"] is True
        assert result["precision"] == 0.85