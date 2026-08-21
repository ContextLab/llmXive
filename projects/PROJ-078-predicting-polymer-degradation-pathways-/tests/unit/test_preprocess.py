"""
Unit tests for preprocess.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from preprocess import (
    is_polyester,
    validate_environmental_data,
    smiles_to_graph_features,
    preprocess_dataset,
    confirm_exclusion_decision
)

class TestIsPolyester:
    def test_polyester_recognized(self):
        """Test that a molecule with ester group is recognized as polyester."""
        smiles = "CC(=O)OCC"  # Simple ester
        assert is_polyester(smiles) is True

    def test_non_polyester_rejected(self):
        """Test that a molecule without ester group is rejected."""
        smiles = "CCCC"  # Alkane
        assert is_polyester(smiles) is False

    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        smiles = "invalid_smiles_123"
        assert is_polyester(smiles) is False

    def test_polymer_with_ester(self):
        """Test a more complex polyester."""
        smiles = "CC(=O)OCCOC(=O)C"  # Diester
        assert is_polyester(smiles) is True

class TestValidateEnvironmentalData:
    def test_valid_data(self):
        """Test record with valid environmental data."""
        record = {
            'temperature': 298.0,
            'ph': 7.0,
            'uv': 0.5
        }
        assert validate_environmental_data(record) is True

    def test_missing_temperature(self):
        """Test record with missing temperature."""
        record = {
            'ph': 7.0,
            'uv': 0.5
        }
        assert validate_environmental_data(record) is False

    def test_missing_ph(self):
        """Test record with missing pH."""
        record = {
            'temperature': 298.0,
            'uv': 0.5
        }
        assert validate_environmental_data(record) is False

    def test_missing_uv(self):
        """Test record with missing UV."""
        record = {
            'temperature': 298.0,
            'ph': 7.0
        }
        assert validate_environmental_data(record) is False

    def test_none_values(self):
        """Test record with None values."""
        record = {
            'temperature': None,
            'ph': 7.0,
            'uv': 0.5
        }
        assert validate_environmental_data(record) is False

    def test_nan_values(self):
        """Test record with NaN values."""
        record = {
            'temperature': float('nan'),
            'ph': 7.0,
            'uv': 0.5
        }
        assert validate_environmental_data(record) is False

    def test_invalid_numeric(self):
        """Test record with non-numeric values."""
        record = {
            'temperature': "hot",
            'ph': 7.0,
            'uv': 0.5
        }
        assert validate_environmental_data(record) is False

class TestSmilesToGraphFeatures:
    def test_simple_molecule(self):
        """Test conversion of a simple molecule."""
        smiles = "CCO"  # Ethanol
        result = smiles_to_graph_features(smiles, 298.0, 7.0, 0.5)
        assert result is not None
        assert 'atom_features' in result
        assert 'bond_features' in result
        assert 'edge_index' in result
        assert 'environment_vector' in result
        assert result['smiles'] == smiles

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None."""
        smiles = "invalid_smiles"
        result = smiles_to_graph_features(smiles, 298.0, 7.0, 0.5)
        assert result is None

    def test_environment_vector(self):
        """Test that environment vector is correctly set."""
        smiles = "CCO"
        temp, ph, uv = 300.0, 6.5, 1.0
        result = smiles_to_graph_features(smiles, temp, ph, uv)
        assert result is not None
        assert result['environment_vector'][0] == temp
        assert result['environment_vector'][1] == ph
        assert result['environment_vector'][2] == uv

class TestPreprocessDataset:
    def test_preprocess_valid_csv(self, tmp_path):
        """Test preprocessing of a valid CSV file."""
        # Create input CSV
        input_path = tmp_path / 'input.csv'
        data = {
            'smiles': ['CC(=O)OCC', 'CCCC', 'CCO'],
            'temperature': [298.0, 300.0, 295.0],
            'ph': [7.0, 6.5, 7.5],
            'uv': [0.5, 0.0, 1.0],
            'degradation_pathway': ['hydrolysis', 'oxidation', 'hydrolysis'],
            'source_id': ['s1', 's2', 's3']
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)

        output_path = tmp_path / 'output.parquet'
        exclusion_log_path = tmp_path / 'exclusion_log.json'

        processed_count, excluded_count = preprocess_dataset(
            input_path, output_path, exclusion_log_path
        )

        # Should have 2 records (one excluded as non-polyester)
        assert processed_count == 2
        assert excluded_count == 0  # No missing env data
        assert output_path.exists()

        # Verify exclusion log
        assert exclusion_log_path.exists()
        with open(exclusion_log_path, 'r') as f:
            log = json.load(f)
        assert log['excluded_non_polyester'] == 1

    def test_excludes_missing_env_data(self, tmp_path):
        """Test that records with missing environmental data are excluded."""
        input_path = tmp_path / 'input.csv'
        data = {
            'smiles': ['CC(=O)OCC', 'CCO'],
            'temperature': [298.0, None],  # Missing temp
            'ph': [7.0, 7.0],
            'uv': [0.5, 1.0],
            'degradation_pathway': ['hydrolysis', 'hydrolysis'],
            'source_id': ['s1', 's2']
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)

        output_path = tmp_path / 'output.parquet'
        exclusion_log_path = tmp_path / 'exclusion_log.json'

        processed_count, excluded_count = preprocess_dataset(
            input_path, output_path, exclusion_log_path
        )

        # Should have 1 record (one excluded due to missing temp)
        assert processed_count == 1
        assert excluded_count == 1

        # Verify exclusion log
        with open(exclusion_log_path, 'r') as f:
            log = json.load(f)
        assert log['excluded_environmental'] == 1

class TestConfirmExclusionDecision:
    def test_confirm_from_log(self, tmp_path):
        """Test confirming exclusion decision from log file."""
        log_path = tmp_path / 'exclusion_log.json'
        log_data = {
            'total_input': 10,
            'excluded_environmental': 2,
            'excluded_non_polyester': 3,
            'failed_conversions': 1,
            'final_count': 4,
            'details': []
        }
        with open(log_path, 'w') as f:
            json.dump(log_data, f)

        result = confirm_exclusion_decision(log_path)
        assert result['exclusion_path_taken'] is True
        assert result['excluded_count'] == 2
        assert result['reason'] == 'missing_environmental_data_hard_exclusion'