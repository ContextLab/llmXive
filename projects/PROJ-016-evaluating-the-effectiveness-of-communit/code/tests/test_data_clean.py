import pytest
import time
import requests
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import json
import tempfile
import os

# Ensure code directory is in path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.classify import load_metadata, classify_regime, convert_to_binary
from data.clean import apply_fr007_exclusion, clean_and_merge_data
import pandas as pd

# Fixtures and Helpers
@pytest.fixture
def temp_metadata_dir():
    """Create a temporary directory with a valid metadata file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        metadata = {
            "indicator_code": "AG.LND.FRST.ZS",
            "source": "World Bank",
            "thresholds": {
                "cbnrm_min": 0.15,
                "cbnrm_max": 0.85,
                "state_led_min": 0.0,
                "state_led_max": 0.15,
                "community_led_min": 0.85,
                "community_led_max": 1.0
            },
            "description": "Test metadata for regime classification"
        }
        metadata_file = tmp_path / "cbnrm_proxy_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        yield tmp_path

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with proxy values to test classification."""
    data = {
        'country': ['USA', 'BRA', 'IND', 'ZAF', 'CAN'],
        'year': [2000, 2000, 2000, 2000, 2000],
        'cbnrm_proxy': [0.05, 0.50, 0.90, 0.10, 0.20], # State, Mixed, Community, State, State
        'gdp_per_capita': [50000, 8000, 2000, 6000, 40000],
        'population_density': [35, 25, 400, 45, 4]
    }
    return pd.DataFrame(data)

class TestRegimeClassificationLogic:
    """
    Unit tests for regime classification logic (threshold mapping).
    Tests the mapping of CBNRM proxy values to binary/multi-class regime types
    based on thresholds loaded from metadata.
    """

    def test_load_metadata_valid_file(self, temp_metadata_dir):
        """Test that load_metadata correctly reads and parses the JSON file."""
        metadata_path = temp_metadata_dir / "cbnrm_proxy_metadata.json"
        metadata = load_metadata(metadata_path)
        
        assert metadata is not None
        assert "thresholds" in metadata
        assert metadata["indicator_code"] == "AG.LND.FRST.ZS"
        assert "state_led_min" in metadata["thresholds"]

    def test_load_metadata_missing_file(self):
        """Test that load_metadata raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_metadata(Path("/nonexistent/path/file.json"))

    def test_classify_regime_state_led(self, temp_metadata_dir, sample_dataframe):
        """
        Test classification of 'State-Led' regime.
        Values: 0.05 (USA), 0.10 (ZAF), 0.20 (CAN - wait, 0.20 is > 0.15? Let's check thresholds).
        Thresholds in fixture: state_led_max = 0.15.
        So 0.05 -> State, 0.10 -> State. 0.20 -> Mixed (since > 0.15 and < 0.85).
        """
        metadata_path = temp_metadata_dir / "cbnrm_proxy_metadata.json"
        metadata = load_metadata(metadata_path)
        
        # Test USA (0.05) -> State Led
        result_usa = classify_regime(sample_dataframe.loc[0, 'cbnrm_proxy'], metadata)
        assert result_usa == "State-Led", f"Expected 'State-Led', got {result_usa}"

        # Test ZAF (0.10) -> State Led
        result_zaf = classify_regime(sample_dataframe.loc[3, 'cbnrm_proxy'], metadata)
        assert result_zaf == "State-Led", f"Expected 'State-Led', got {result_zaf}"

    def test_classify_regime_community_led(self, temp_metadata_dir, sample_dataframe):
        """
        Test classification of 'Community-Led' regime.
        Value: 0.90 (IND). Threshold: community_led_min = 0.85.
        """
        metadata_path = temp_metadata_dir / "cbnrm_proxy_metadata.json"
        metadata = load_metadata(metadata_path)

        result_ind = classify_regime(sample_dataframe.loc[2, 'cbnrm_proxy'], metadata)
        assert result_ind == "Community-Led", f"Expected 'Community-Led', got {result_ind}"

    def test_classify_regime_mixed(self, temp_metadata_dir, sample_dataframe):
        """
        Test classification of 'Mixed' regime.
        Value: 0.50 (BRA). Threshold: 0.15 < 0.50 < 0.85.
        """
        metadata_path = temp_metadata_dir / "cbnrm_proxy_metadata.json"
        metadata = load_metadata(metadata_path)

        result_bra = classify_regime(sample_dataframe.loc[1, 'cbnrm_proxy'], metadata)
        assert result_bra == "Mixed", f"Expected 'Mixed', got {result_bra}"
        
        # Test CAN (0.20) -> Mixed (since > 0.15)
        result_can = classify_regime(sample_dataframe.loc[4, 'cbnrm_proxy'], metadata)
        assert result_can == "Mixed", f"Expected 'Mixed', got {result_can}"

    def test_classify_regime_boundary_values(self, temp_metadata_dir):
        """
        Test classification exactly at boundaries.
        Thresholds: State max 0.15, Mixed max 0.85.
        """
        metadata_path = temp_metadata_dir / "cbnrm_proxy_metadata.json"
        metadata = load_metadata(metadata_path)

        # Exactly at state_led_max (0.15) -> Should be State-Led (inclusive lower, exclusive upper usually, but logic defines ranges)
        # Based on typical logic: [0.0, 0.15] -> State, (0.15, 0.85) -> Mixed, [0.85, 1.0] -> Community
        # Let's verify the implementation handles the boundary as defined in classify.py logic
        # Assuming classify.py uses: if val <= state_max: State; elif val < comm_min: Mixed; else: Community
        
        # Test 0.15 (Boundary State/Mixed)
        # If logic is <= 0.15 -> State
        result_boundary_1 = classify_regime(0.15, metadata)
        assert result_boundary_1 == "State-Led", f"Boundary 0.15 expected State-Led, got {result_boundary_1}"

        # Test 0.1500001 (Just above State)
        result_above_1 = classify_regime(0.1500001, metadata)
        assert result_above_1 == "Mixed", f"Just above 0.15 expected Mixed, got {result_above_1}"

        # Test 0.85 (Boundary Mixed/Community)
        # If logic is < 0.85 -> Mixed, >= 0.85 -> Community
        result_boundary_2 = classify_regime(0.85, metadata)
        assert result_boundary_2 == "Community-Led", f"Boundary 0.85 expected Community-Led, got {result_boundary_2}"

    def test_convert_to_binary_state_vs_community(self, temp_metadata_dir):
        """
        Test binary conversion logic.
        Typically: State-Led -> 0, Community-Led/Mixed -> 1 (or similar).
        We need to verify the specific mapping defined in convert_to_binary.
        Assuming: State-Led = 0, others = 1 for binary comparison.
        """
        metadata_path = temp_metadata_dir / "cbnrm_proxy_metadata.json"
        metadata = load_metadata(metadata_path)

        # State-Led
        assert convert_to_binary("State-Led") == 0
        # Mixed
        assert convert_to_binary("Mixed") == 1
        # Community-Led
        assert convert_to_binary("Community-Led") == 1

    def test_convert_to_binary_invalid(self, temp_metadata_dir):
        """Test that invalid regime types raise an error or return a specific value."""
        with pytest.raises(ValueError):
            convert_to_binary("Invalid_Regime_Type")

    def test_full_pipeline_classification(self, temp_metadata_dir, sample_dataframe):
        """
        Test the full pipeline: Load metadata -> Classify -> Convert to Binary.
        """
        metadata_path = temp_metadata_dir / "cbnrm_proxy_metadata.json"
        metadata = load_metadata(metadata_path)

        # Apply classification to the dataframe
        sample_dataframe['regime_type'] = sample_dataframe['cbnrm_proxy'].apply(
            lambda x: classify_regime(x, metadata)
        )
        
        # Verify specific rows
        assert sample_dataframe.loc[0, 'regime_type'] == "State-Led"
        assert sample_dataframe.loc[1, 'regime_type'] == "Mixed"
        assert sample_dataframe.loc[2, 'regime_type'] == "Community-Led"

        # Convert to binary
        sample_dataframe['regime_binary'] = sample_dataframe['regime_type'].apply(convert_to_binary)
        
        assert sample_dataframe.loc[0, 'regime_binary'] == 0
        assert sample_dataframe.loc[1, 'regime_binary'] == 1
        assert sample_dataframe.loc[2, 'regime_binary'] == 1