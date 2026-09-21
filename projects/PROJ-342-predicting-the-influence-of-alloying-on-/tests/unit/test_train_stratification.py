import pytest
import logging
import io
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from train import check_family_stratification, get_project_root

class TestFamilyStratification:
    """
    Test suite for T087: Family Stratification Edge Case Test.
    
    Simulates datasets with families having small (<50), medium (>=50, <200), 
    and large (>=200) sample counts to verify the STRATIFICATION_WARNING 
    logic in check_family_stratification.
    """

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = logging.getLogger("train")
        self.logger.setLevel(logging.WARNING)
        
        # Create a mock handler to capture logs
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.WARNING)
        self.logger.addHandler(self.handler)

    def teardown_method(self):
        """Clean up after tests."""
        self.logger.removeHandler(self.handler)
        self.log_capture.close()

    def _create_mock_dataframe(self, family_counts: dict) -> pd.DataFrame:
        """
        Create a mock DataFrame with specified family counts.
        
        Args:
            family_counts: Dict mapping family name to sample count
        
        Returns:
            Mock DataFrame with 'family' column
        """
        data = {"family": []}
        for family, count in family_counts.items():
            data["family"].extend([family] * count)
        
        # Add dummy columns required by load_prepared_data if called
        df = pd.DataFrame(data)
        df["Tg"] = 500.0  # Dummy target
        df["radius_mismatch"] = 0.1
        df["electronegativity_diff"] = 0.5
        df["VEC"] = 7.5
        return df

    def test_stratification_warning_small_family(self):
        """
        Test that families with N < 50 trigger STRATIFICATION_WARNING.
        
        Scenario: One family with 20 samples, one with 100.
        Expected: Warning for the small family.
        """
        # Arrange
        mock_df = self._create_mock_dataframe({
            "small_family": 20,
            "medium_family": 100
        })
        
        # Act
        # We mock load_prepared_data to return our mock_df
        with patch("train.load_prepared_data", return_value=mock_df):
            # Call the function (it expects a path, but we mock the loader)
            # The function signature is check_family_stratification(data_path)
            # but it internally loads data. We need to patch the loader inside.
            # Actually, let's call the logic directly by passing the df to a 
            # helper or mocking the internal load.
            
            # Re-implementing the logic inline for testing clarity
            # The actual function check_family_stratification calls load_prepared_data
            # Let's mock that call specifically
            pass

        # Alternative approach: Mock the function that does the work
        # We will patch the internal logic or call a version that accepts df
        # Since the task requires testing the existing function, we mock load_prepared_data
        
        with patch("train.load_prepared_data", return_value=mock_df):
            # The function check_family_stratification takes a path, loads data, then checks
            # We pass a dummy path
            check_family_stratification("/fake/path/to/data.csv")

        # Assert
        log_contents = self.log_capture.getvalue()
        assert "STRATIFICATION_WARNING" in log_contents, \
            f"Expected STRATIFICATION_WARNING in log, got: {log_contents}"
        assert "small_family" in log_contents, \
            f"Expected 'small_family' in log, got: {log_contents}"
        assert "20" in log_contents, \
            f"Expected sample count '20' in log, got: {log_contents}"

    def test_stratification_no_warning_large_families(self):
        """
        Test that families with N >= 50 proceed without warning.
        
        Scenario: Two families, one with 50, one with 200.
        Expected: No warnings logged.
        """
        # Arrange
        mock_df = self._create_mock_dataframe({
            "min_family": 50,
            "large_family": 200
        })
        
        # Reset log capture
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.logger.addHandler(self.handler)

        # Act
        with patch("train.load_prepared_data", return_value=mock_df):
            check_family_stratification("/fake/path/to/data.csv")

        # Assert
        log_contents = self.log_capture.getvalue()
        assert "STRATIFICATION_WARNING" not in log_contents, \
            f"Unexpected warning in log: {log_contents}"

    def test_stratification_mixed_counts(self):
        """
        Test a dataset with small, medium, and large families.
        
        Scenario:
        - small: 10 samples (should warn)
        - medium: 150 samples (no warn)
        - large: 500 samples (no warn)
        
        Expected: Warning only for 'small'.
        """
        # Arrange
        mock_df = self._create_mock_dataframe({
            "tiny": 10,
            "medium": 150,
            "huge": 500
        })
        
        # Reset log capture
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.logger.addHandler(self.handler)

        # Act
        with patch("train.load_prepared_data", return_value=mock_df):
            check_family_stratification("/fake/path/to/data.csv")

        # Assert
        log_contents = self.log_capture.getvalue()
        
        # Should warn for tiny
        assert "STRATIFICATION_WARNING" in log_contents
        assert "tiny" in log_contents
        assert "10" in log_contents
        
        # Should NOT warn for medium or huge
        # We verify that the warning message specifically mentions the small one
        # and doesn't mention the others in a warning context (though they might appear in logs)
        # The safest check is that the warning count corresponds to the small families
        # But simpler: ensure the warning text contains the small family details
        assert "Sample count: 10" in log_contents or "10 samples" in log_contents

    def test_stratification_exact_threshold_49(self):
        """
        Test boundary condition: N=49 should warn.
        """
        mock_df = self._create_mock_dataframe({"boundary": 49})
        
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.logger.addHandler(self.handler)

        with patch("train.load_prepared_data", return_value=mock_df):
            check_family_stratification("/fake/path/to/data.csv")

        log_contents = self.log_capture.getvalue()
        assert "STRATIFICATION_WARNING" in log_contents
        assert "49" in log_contents

    def test_stratification_exact_threshold_50(self):
        """
        Test boundary condition: N=50 should NOT warn.
        """
        mock_df = self._create_mock_dataframe({"boundary": 50})
        
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.logger.addHandler(self.handler)

        with patch("train.load_prepared_data", return_value=mock_df):
            check_family_stratification("/fake/path/to/data.csv")

        log_contents = self.log_capture.getvalue()
        assert "STRATIFICATION_WARNING" not in log_contents