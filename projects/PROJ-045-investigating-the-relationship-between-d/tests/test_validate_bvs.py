import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock pymatgen components for testing without heavy dependencies in unit tests if needed,
# but here we assume pymatgen is installed as per requirements.txt.
# We will create a mock structure for testing the logic.

from validate import calculate_bvs_deviation, validate_bvs, setup_validate_logging

def test_calculate_bvs_deviation():
    """Test BVS deviation calculation logic."""
    # We need a mock structure. Since creating a real Structure might be heavy,
    # we can mock the necessary parts or use a small real one if available.
    # For this test, we assume a simple mock structure that mimics the interface.
    
    # Create a mock structure
    mock_structure = MagicMock()
    mock_structure.oxi_state_guesses = None
    
    # Mock the add_oxidation_state_by_guess to do nothing
    mock_structure.add_oxidation_state_by_guess = MagicMock()
    
    # Mock the site species
    mock_site = MagicMock()
    mock_site.species_string = "Li"
    mock_structure.__iter__ = MagicMock(return_value=iter([mock_site]))
    mock_structure.__len__ = MagicMock(return_value=1)
    mock_structure.__getitem__ = MagicMock(return_value=mock_site)

    # Mock BVAnalyzer
    with patch('validate.BVAnalyzer') as MockBVAnalyzer:
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.get_bv_sum.return_value = [1.05] # 1.05 vs ideal 1.0 -> 5% deviation
        MockBVAnalyzer.return_value = mock_analyzer_instance

        deviation = calculate_bvs_deviation(mock_structure, "Li", 1.0)
        
        assert deviation == 0.05
        assert deviation <= 0.10 # Should pass 10% threshold

def test_validate_bvs_pass():
    """Test BVS validation passing case."""
    mock_structure = MagicMock()
    mock_structure.oxi_state_guesses = None
    mock_structure.add_oxidation_state_by_guess = MagicMock()
    
    mock_site = MagicMock()
    mock_site.species_string = "Li"
    mock_structure.__iter__ = MagicMock(return_value=iter([mock_site]))
    mock_structure.__len__ = MagicMock(return_value=1)
    mock_structure.__getitem__ = MagicMock(return_value=mock_site)

    config = {
        "validation": {
            "bvs": {
                "threshold_percent": 10.0,
                "element_checks": [
                    {"element": "Li", "ideal_oxidation_state": 1.0}
                ]
            }
        }
    }

    with patch('validate.BVAnalyzer') as MockBVAnalyzer:
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.get_bv_sum.return_value = [1.02] # 2% deviation
        MockBVAnalyzer.return_value = mock_analyzer_instance

        logger = setup_validate_logging()
        result = validate_bvs(mock_structure, config, logger)

        assert result["passed"] is True
        assert result["failed_reason"] is None

def test_validate_bvs_fail():
    """Test BVS validation failing case."""
    mock_structure = MagicMock()
    mock_structure.oxi_state_guesses = None
    mock_structure.add_oxidation_state_by_guess = MagicMock()
    
    mock_site = MagicMock()
    mock_site.species_string = "Li"
    mock_structure.__iter__ = MagicMock(return_value=iter([mock_site]))
    mock_structure.__len__ = MagicMock(return_value=1)
    mock_structure.__getitem__ = MagicMock(return_value=mock_site)

    config = {
        "validation": {
            "bvs": {
                "threshold_percent": 10.0,
                "element_checks": [
                    {"element": "Li", "ideal_oxidation_state": 1.0}
                ]
            }
        }
    }

    with patch('validate.BVAnalyzer') as MockBVAnalyzer:
        mock_analyzer_instance = MagicMock()
        mock_analyzer_instance.get_bv_sum.return_value = [1.15] # 15% deviation
        MockBVAnalyzer.return_value = mock_analyzer_instance

        logger = setup_validate_logging()
        result = validate_bvs(mock_structure, config, logger)

        assert result["passed"] is False
        assert "BVS deviation" in result["failed_reason"]