"""
Unit tests for preprocess.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from rdkit import Chem

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from preprocess import is_polyester, smiles_to_graph_features, validate_environmental_data, preprocess_dataset

class TestIsPolyester:
    def test_polyester_detection(self):
        """Test that polyester SMILES are correctly identified."""
        # Valid polyester (has ester group C(=O)O)
        smiles_polyester = "CC(=O)OCC"  # Ethyl acetate (simple ester)
        assert is_polyester(smiles_polyester) is True

        # Non-polyester (no ester group)
        smiles_non_polyester = "CCCC"  # Butane
        assert is_polyester(smiles_non_polyester) is False

        # Invalid SMILES
        assert is_polyester("INVALID") is False

    def test_complex_polyester(self):
        """Test complex polyester detection."""
        # Polyethylene terephthalate (PET) monomer
        smiles_pet = "O=C(Oc1ccc(C(=O)O)cc1)Oc1ccc(C(=O)O)cc1"
        assert is_polyester(smiles_pet) is True

class TestSmilesToGraphFeatures:
    def test_graph_conversion(self):
        """Test conversion of SMILES to graph features."""
        smiles = "CCO"  # Ethanol
        mol = Chem.MolFromSmiles(smiles)
        graph_data = smiles_to_graph_features(mol)

        assert graph_data is not None
        assert 'atom_features' in graph_data
        assert 'bond_features' in graph_data
        assert 'edge_index' in graph_data
        assert 'smiles' in graph_data

        # Check dimensions
        assert graph_data['atom_features'].shape[1] == 5  # 5 features per atom
        assert graph_data['bond_features'].shape[1] == 3  # 3 features per bond

    def test_single_atom(self):
        """Test conversion of single atom molecule."""
        smiles = "[He]"
        mol = Chem.MolFromSmiles(smiles)
        graph_data = smiles_to_graph_features(mol)

        assert graph_data is not None
        assert graph_data['atom_features'].shape[0] == 1
        assert graph_data['bond_features'].shape[0] == 0

class TestValidateEnvironmentalData:
    def test_complete_data(self):
        """Test validation with complete environmental data."""
        row = pd.Series({
            'temperature': 30.0,
            'ph': 6.5,
            'uv': 10.0
        })
        is_valid, imputed, missing = validate_environmental_data(row)
        assert is_valid is True
        assert missing == []
        assert imputed['temperature'] == 30.0

    def test_missing_temperature(self):
        """Test imputation of missing temperature."""
        row = pd.Series({
            'temperature': None,
            'ph': 6.5,
            'uv': 10.0
        })
        is_valid, imputed, missing = validate_environmental_data(row)
        assert is_valid is False
        assert 'temperature' in missing
        assert imputed['temperature'] == 25.0  # Default

    def test_missing_all_env(self):
        """Test imputation of all missing environmental data."""
        row = pd.Series({
            'temperature': None,
            'ph': None,
            'uv': None
        })
        is_valid, imputed, missing = validate_environmental_data(row)
        assert is_valid is False
        assert len(missing) == 3
        assert imputed['temperature'] == 25.0
        assert imputed['ph'] == 7.0
        assert imputed['uv'] == 0.0

class TestPreprocessDataset:
    def test_preprocess_basic(self):
        """Test basic preprocessing pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.parquet"

            # Create test data
            data = {
                'smiles': ['CC(=O)OCC', 'CCCC', 'O=C(Oc1ccc(C(=O)O)cc1)Oc1ccc(C(=O)O)cc1'],
                'degradation_pathway': ['hydrolysis', 'oxidation', 'photolysis'],
                'temperature': [25.0, 30.0, None],
                'ph': [7.0, None, 6.0],
                'uv': [0.0, 10.0, 5.0]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)

            # Run preprocessing
            result = preprocess_dataset(input_path, output_path)

            # Verify output
            assert output_path.exists()
            output_df = pd.read_parquet(output_path)

            # Should have 2 polyesters (first and third), second is non-polyester
            assert len(output_df) == 2
            assert 'atom_features' in output_df.columns
            assert 'temperature' in output_df.columns

            # Check imputation
            assert output_df.loc[output_df['smiles'] == 'O=C(Oc1ccc(C(=O)O)cc1)Oc1ccc(C(=O)O)cc1', 'temperature'].iloc[0] == 25.0

            # Check exclusion log
            exclusion_log_path = output_path.parent / 'exclusion_decision_log.json'
            assert exclusion_log_path.exists()
            with open(exclusion_log_path, 'r') as f:
                log = json.load(f)
            assert log['excluded_count'] >= 1

    def test_missing_env_imputation(self):
        """Test that missing environmental data is flagged and imputed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.parquet"

            data = {
                'smiles': ['CC(=O)OCC'],
                'degradation_pathway': ['hydrolysis'],
                'temperature': [None],
                'ph': [None],
                'uv': [None]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)

            result = preprocess_dataset(input_path, output_path)

            # Check env missing flags
            env_missing_path = output_path.parent / 'flagged_env_missing.csv'
            assert env_missing_path.exists()
            env_df = pd.read_csv(env_missing_path)
            assert len(env_df) == 1
            assert 'temperature' in env_df['missing_fields'].iloc[0]

    def test_non_polyester_exclusion(self):
        """Test that non-polyesters are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.parquet"

            data = {
                'smiles': ['CCCC', 'CC(=O)OCC'],
                'degradation_pathway': ['oxidation', 'hydrolysis'],
                'temperature': [30.0, 25.0],
                'ph': [7.0, 7.0],
                'uv': [10.0, 0.0]
            }
            df = pd.DataFrame(data)
            df.to_csv(input_path, index=False)

            result = preprocess_dataset(input_path, output_path)

            output_df = pd.read_parquet(output_path)
            assert len(output_df) == 1
            assert output_df['smiles'].iloc[0] == 'CC(=O)OCC'