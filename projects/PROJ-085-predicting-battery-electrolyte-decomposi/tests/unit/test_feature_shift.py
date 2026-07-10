"""
Unit tests for T024: Feature Shift Analysis (High-Voltage Specific Descriptors)
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np

# Import the module under test
from models.feature_shift import (
    get_top_n_features,
    identify_high_voltage_specific_features,
    run_shift_analysis_pipeline,
    load_feature_importance_from_run
)


@pytest.fixture
def mock_importance_data():
    """Create mock importance data matching model_run.json structure."""
    return {
        'importance': {
            'low': {
                'homo_eV': 0.85,
                'lumo_eV': 0.72,
                'band_gap_eV': 0.65,
                'bond_length_c1_o1': 0.45,
                'dihedral_c1_c2_o1_o2': 0.30,
                'angle_c1_c2_c3': 0.25
            },
            'high': {
                'homo_eV': 0.40,
                'lumo_eV': 0.35,
                'solvent_dipole': 0.90,
                'polarizability': 0.88,
                'bond_length_c1_o1': 0.50,
                'angle_c1_c2_c3': 0.30
            }
        },
        'model_config': {
            'n_estimators': 100,
            'max_depth': 20
        }
    }


@pytest.fixture
def mock_model_run_path(tmp_path, mock_importance_data):
    """Create a temporary model_run.json file."""
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    model_run_file = processed_dir / "model_run.json"
    with open(model_run_file, 'w') as f:
        json.dump(mock_importance_data, f)
    return model_run_file


class TestGetTopNFeatures:
    """Tests for get_top_n_features function."""

    def test_get_top_3_features(self, mock_importance_data):
        """Test extracting top 3 features from a bin."""
        top_3 = get_top_n_features(mock_importance_data, 'low', n=3)

        assert len(top_3) == 3
        assert top_3[0] == 'homo_eV'  # Highest score
        assert top_3[1] == 'lumo_eV'
        assert top_3[2] == 'band_gap_eV'

    def test_get_top_1_feature(self, mock_importance_data):
        """Test extracting top 1 feature."""
        top_1 = get_top_n_features(mock_importance_data, 'high', n=1)

        assert len(top_1) == 1
        assert top_1[0] == 'solvent_dipole'

    def test_invalid_bin_name(self, mock_importance_data):
        """Test that invalid bin name raises ValueError."""
        with pytest.raises(ValueError, match="Bin 'invalid' not found"):
            get_top_n_features(mock_importance_data, 'invalid', n=3)

    def test_missing_importance_key(self):
        """Test that missing 'importance' key raises KeyError."""
        invalid_data = {'model_config': {}}
        with pytest.raises(KeyError, match="'importance' key missing"):
            get_top_n_features(invalid_data, 'low', n=3)


class TestIdentifyHighVoltageSpecificFeatures:
    """Tests for identify_high_voltage_specific_features function."""

    def test_identify_high_specific_features(self, mock_importance_data):
        """Test identifying features unique to high-potential top 3."""
        result = identify_high_voltage_specific_features(
            mock_importance_data,
            low_bins=['low'],
            high_bins=['high'],
            top_n=3
        )

        # High top 3: solvent_dipole, polarizability, homo_eV (or lumo_eV depending on sort)
        # Low top 3: homo_eV, lumo_eV, band_gap_eV
        # High-specific should be: solvent_dipole, polarizability (not in low top 3)

        assert 'deviation_note' in result
        assert '4V' in result['deviation_note']
        assert '3-5V' in result['deviation_note']

        # Check that high-specific features are in high top but not low top
        for feat in result['high_specific']:
            assert feat in result['high_top_n']
            assert feat not in result['low_top_n']

    def test_no_high_specific_features(self):
        """Test case where high and low have identical top features."""
        same_data = {
            'importance': {
                'low': {'a': 0.9, 'b': 0.8, 'c': 0.7, 'd': 0.6},
                'high': {'a': 0.9, 'b': 0.8, 'c': 0.7, 'd': 0.6}
            }
        }

        result = identify_high_voltage_specific_features(
            same_data,
            low_bins=['low'],
            high_bins=['high'],
            top_n=3
        )

        assert result['high_specific'] == []
        assert result['high_top_n'] == ['a', 'b', 'c']
        assert result['low_top_n'] == ['a', 'b', 'c']

    def test_multiple_low_bins(self, mock_importance_data):
        """Test with multiple low bins (union of top features)."""
        multi_low_data = {
            'importance': {
                'low_0v': {'a': 0.9, 'b': 0.8, 'c': 0.7},
                'low_2v': {'b': 0.9, 'c': 0.8, 'd': 0.7},
                'high': {'e': 0.9, 'f': 0.8, 'g': 0.7}
            }
        }

        result = identify_high_voltage_specific_features(
            multi_low_data,
            low_bins=['low_0v', 'low_2v'],
            high_bins=['high'],
            top_n=3
        )

        # Low union: a, b, c, d
        # High: e, f, g
        # High-specific: e, f, g (all of them)
        assert set(result['high_specific']) == {'e', 'f', 'g'}

    def test_deviation_note_content(self, mock_importance_data):
        """Test that deviation note contains required information."""
        result = identify_high_voltage_specific_features(mock_importance_data)

        note = result['deviation_note']
        assert '3-5V' in note
        assert '4V' in note
        assert 'data constraints' in note


class TestRunShiftAnalysisPipeline:
    """Tests for the full pipeline function."""

    @patch('models.feature_shift.get_output_dir')
    @patch('models.feature_shift.load_feature_importance_from_run')
    def test_run_pipeline_success(self, mock_load, mock_get_output, mock_model_run_path, tmp_path):
        """Test successful pipeline execution."""
        mock_load.return_value = {
            'importance': {
                'low': {'a': 0.9, 'b': 0.8},
                'high': {'c': 0.9, 'd': 0.8}
            }
        }

        mock_output_dir = tmp_path / "output"
        mock_get_output.return_value = mock_output_dir

        result = run_shift_analysis_pipeline(
            low_bins=['low'],
            high_bins=['high'],
            top_n=2
        )

        assert 'high_specific' in result
        assert 'deviation_note' in result

        # Check that output file was created
        expected_output = mock_output_dir / "validation" / "feature_shift_analysis.json"
        assert expected_output.exists()

    @patch('models.feature_shift.get_output_dir')
    def test_run_pipeline_missing_artifact(self, mock_get_output, tmp_path):
        """Test pipeline fails gracefully when model_run.json is missing."""
        mock_output_dir = tmp_path / "output"
        mock_get_output.return_value = mock_output_dir

        with patch('models.feature_shift.get_data_dir') as mock_data_dir:
            mock_data_path = tmp_path / "nonexistent"
            mock_data_dir.return_value = mock_data_path

            with pytest.raises(FileNotFoundError, match="Model run artifact not found"):
                run_shift_analysis_pipeline()
