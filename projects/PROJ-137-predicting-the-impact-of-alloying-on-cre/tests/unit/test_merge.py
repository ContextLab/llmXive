"""
Unit tests for thermodynamic descriptor calculation and merging.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from src.data.merge import calculate_thermodynamic_descriptors, merge_thermodynamic_data


class TestCalculateThermodynamicDescriptors:
    """Tests for the calculate_thermodynamic_descriptors function."""

    @patch("src.data.merge.Composition")
    @patch("src.data.merge.MPRester")
    def test_successful_calculation(self, mock_mpr, mock_composition):
        """Test successful calculation with mocked MP API."""
        # Setup mocks
        mock_comp = MagicMock()
        mock_comp.keys.return_value = ["Fe", "Cr"]
        mock_comp.values.return_value = [0.5, 0.5]
        mock_composition.return_value = mock_comp

        mock_entry = MagicMock()
        mock_entry.energy_per_atom = -0.5
        mock_mpr.return_value.__enter__.return_value.get_entries_in_chemsys.return_value = [
            mock_entry
        ]

        # Mock atomic radii
        with patch("src.data.merge.Composition") as MockComp:
            MockComp.return_value.atomic_radii = [1.24, 1.28]  # Fe, Cr radii

            result = calculate_thermodynamic_descriptors("Fe0.5Cr0.5", "fake_key")

            # Should return a tuple of floats
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert result[0] is not None  # mixing enthalpy
            assert result[1] is not None  # radius mismatch

    @patch("src.data.merge.Composition")
    def test_missing_api_key_fallback(self, mock_composition):
        """Test fallback behavior when API key is missing."""
        mock_comp = MagicMock()
        mock_comp.keys.return_value = ["Fe"]
        mock_comp.values.return_value = [1.0]
        mock_composition.return_value = mock_comp

        result = calculate_thermodynamic_descriptors("Fe1.0")

        # Should return (0.0, radius) for simplified estimation
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Mixing enthalpy should be 0.0 for fallback
        assert result[0] == 0.0

    @patch("src.data.merge.Composition")
    def test_invalid_composition(self, mock_composition):
        """Test handling of invalid composition strings."""
        mock_composition.side_effect = Exception("Invalid composition")

        result = calculate_thermodynamic_descriptors("InvalidComposition")

        # Should return (None, None) on error
        assert result == (None, None)


class TestMergeThermodynamicData:
    """Tests for the merge_thermodynamic_data function."""

    @pytest.fixture
    def sample_input_data(self, tmp_path):
        """Create sample input CSV for testing."""
        input_file = tmp_path / "input.csv"
        data = {
            "alloy_id": [1, 2, 3],
            "composition_str": ["Fe0.5Cr0.5", "Ni0.8Cu0.2", "Ti0.5Al0.5"],
            "temperature": [800, 900, 700],
            "stress": [100, 150, 120],
            "rupture_time": [1000, 2000, 1500],
        }
        df = pd.DataFrame(data)
        df.to_csv(input_file, index=False)
        return input_file

    @patch("src.data.merge.calculate_thermodynamic_descriptors")
    @patch("src.data.merge.load_config")
    def test_merge_success(
        self, mock_load_config, mock_calc_desc, sample_input_data, tmp_path
    ):
        """Test successful merge of thermodynamic data."""
        # Mock config
        mock_load_config.return_value = {
            "materials_project": {"api_key": "fake_key"}
        }

        # Mock descriptor calculations
        mock_calc_desc.side_effect = [
            (-0.1, 0.05),  # Fe-Cr
            (-0.08, 0.03),  # Ni-Cu
            (-0.12, 0.06),  # Ti-Al
        ]

        output_file = tmp_path / "output.csv"

        merge_thermodynamic_data(
            str(sample_input_data), str(output_file), "config/settings.yaml"
        )

        # Verify output file exists
        assert output_file.exists()

        # Verify output content
        result_df = pd.read_csv(output_file)
        assert len(result_df) == 3
        assert "mixing_enthalpy" in result_df.columns
        assert "radius_mismatch" in result_df.columns
        assert result_df["mixing_enthalpy"].notna().sum() == 3

    @patch("src.data.merge.load_config")
    def test_missing_input_columns(self, mock_load_config, tmp_path):
        """Test error when input data is missing required columns."""
        mock_load_config.return_value = {}

        input_file = tmp_path / "input.csv"
        data = {
            "alloy_id": [1, 2],
            # Missing composition_str
        }
        pd.DataFrame(data).to_csv(input_file, index=False)

        output_file = tmp_path / "output.csv"

        with pytest.raises(ValueError) as excinfo:
            merge_thermodynamic_data(
                str(input_file), str(output_file), "config/settings.yaml"
            )

        assert "Missing required columns" in str(excinfo.value)

    @patch("src.data.merge.calculate_thermodynamic_descriptors")
    @patch("src.data.merge.load_config")
    def test_partial_failure_handling(
        self, mock_load_config, mock_calc_desc, sample_input_data, tmp_path
    ):
        """Test handling when some descriptor calculations fail."""
        mock_load_config.return_value = {
            "materials_project": {"api_key": "fake_key"}
        }

        # Mock some failures
        mock_calc_desc.side_effect = [
            (-0.1, 0.05),  # Success
            (None, None),  # Failure
            (-0.12, 0.06),  # Success
        ]

        output_file = tmp_path / "output.csv"

        merge_thermodynamic_data(
            str(sample_input_data), str(output_file), "config/settings.yaml"
        )

        result_df = pd.read_csv(output_file)
        assert len(result_df) == 3
        # One row should have NaN values
        assert result_df["mixing_enthalpy"].isna().sum() == 1
