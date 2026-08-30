"""
Unit tests for data ingestion logic.
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config import N_NOVEL_SAMPLES, ELEMENT_SUBSET

class TestFilterMinElements:
    """Tests for the filter_min_elements logic."""

    def test_filter_removes_single_element(self):
        """Verify that single-element systems are filtered out."""
        # Import the function dynamically to avoid circular imports if any
        from code.data_ingestion import filter_min_elements
        
        # Mock data
        data = [
            {"composition": "Fe", "elements": ["Fe"]},
            {"composition": "FeCo", "elements": ["Fe", "Co"]},
            {"composition": "FeCoNi", "elements": ["Fe", "Co", "Ni"]}
        ]
        
        # Filter for at least 2 elements
        result = filter_min_elements(data, min_elements=2)
        
        assert len(result) == 2
        assert result[0]["composition"] == "FeCo"
        assert result[1]["composition"] == "FeCoNi"

    def test_filter_removes_two_element(self):
        """Verify that two-element systems are filtered out when min is 3."""
        from code.data_ingestion import filter_min_elements

        data = [
            {"composition": "FeCo", "elements": ["Fe", "Co"]},
            {"composition": "FeCoNi", "elements": ["Fe", "Co", "Ni"]}
        ]

        result = filter_min_elements(data, min_elements=3)

        assert len(result) == 1
        assert result[0]["composition"] == "FeCoNi"

class TestFailLoudly:
    """Tests to verify that the ingestion fails loudly without synthetic fallback."""

    def test_load_hmao_dataset_fails_on_error(self):
        """
        Verify that load_hmao_dataset raises an exception when the dataset fetch fails.
        This ensures no synthetic data generation or fallback logic exists.
        """
        from code.data_ingestion import load_hmao_dataset
        
        # Mock the datasets.load_dataset to raise an error
        with patch('code.data_ingestion.load_dataset') as mock_load:
            mock_load.side_effect = ConnectionError("Failed to fetch dataset")
            
            # The function should raise the exception, not return synthetic data
            with pytest.raises(ConnectionError):
                load_hmao_dataset()

    def test_no_synthetic_fallback_on_failure(self):
        """
        Verify that when the fetch fails, the code does NOT generate synthetic data.
        We check that the function raises before any synthetic generation could happen.
        """
        from code.data_ingestion import load_hmao_dataset
        
        with patch('code.data_ingestion.load_dataset') as mock_load:
            mock_load.side_effect = ValueError("Dataset not found")
            
            with pytest.raises(ValueError):
                load_hmao_dataset()
