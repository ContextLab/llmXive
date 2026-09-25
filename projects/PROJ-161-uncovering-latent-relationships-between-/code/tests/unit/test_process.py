import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.process import canonicalize_smiles, calculate_descriptors, merge_structure_and_resistance, process_compounds


class TestCanonicalizeSmiles:
    def test_valid_smiles(self):
        # Valid benzene
        smiles = "c1ccccc1"
        result = canonicalize_smiles(smiles)
        assert result is not None
        assert len(result) > 0

    def test_invalid_smiles(self):
        result = canonicalize_smiles("invalid_smiles_string")
        assert result is None

    def test_none_input(self):
        result = canonicalize_smiles(None)
        assert result is None

    def test_empty_string(self):
        result = canonicalize_smiles("")
        assert result is None

    def test_nan_input(self):
        result = canonicalize_smiles(np.nan)
        assert result is None


class TestCalculateDescriptors:
    def test_calculate_descriptors_returns_dict(self):
        smiles = "CCO"  # Ethanol
        descs = calculate_descriptors(smiles)
        assert isinstance(descs, dict)
        assert len(descs) > 0
        # Check for some common descriptors
        assert "MolWt" in descs or "ExactMolWt" in descs or any("Wt" in k for k in descs.keys())

    def test_invalid_smiles_returns_empty(self):
        descs = calculate_descriptors("invalid")
        assert descs == {}


class TestProcessCompounds:
    def test_process_compounds_excludes_invalid(self):
        data = {
            'smiles': ['c1ccccc1', 'invalid', 'CCO', ''],
            'source': ['chembl', 'chembl', 'chembl', 'chembl']
        }
        df = pd.DataFrame(data)
        result = process_compounds(df)
        
        # Should exclude 'invalid' and ''
        assert len(result) == 2
        assert 'inchi_key' in result.columns
        assert 'canonical_smiles' in result.columns
        assert all(result['inchi_key'].notna())

    def test_process_compounds_empty_input(self):
        df = pd.DataFrame(columns=['smiles'])
        result = process_compounds(df)
        assert result.empty


class TestMergeStructureAndResistance:
    @pytest.fixture
    def sample_structure(self):
        return pd.DataFrame({
            'inchi_key': ['KEY1', 'KEY2', 'KEY3'],
            'mol_wt': [100.0, 200.0, 300.0]
        })

    @pytest.fixture
    def sample_resistance(self):
        return pd.DataFrame({
            'inchi_key': ['KEY1', 'KEY3', 'KEY4'],
            'resistance_score': [0.8, 0.2, 0.9]
        })

    def test_merge_on_inchi_key(self, sample_structure, sample_resistance):
        merged, metrics = merge_structure_and_resistance(sample_structure, sample_resistance)
        
        # KEY1 and KEY3 should match. KEY2 should have NaN resistance.
        assert len(merged) == 3
        assert 'resistance_score' in merged.columns
        
        # Check specific values
        key1_row = merged[merged['inchi_key'] == 'KEY1'].iloc[0]
        assert key1_row['resistance_score'] == 0.8
        
        key2_row = merged[merged['inchi_key'] == 'KEY2'].iloc[0]
        assert pd.isna(key2_row['resistance_score'])
        
        key3_row = merged[merged['inchi_key'] == 'KEY3'].iloc[0]
        assert key3_row['resistance_score'] == 0.2

    def test_metrics_calculation(self, sample_structure, sample_resistance):
        _, metrics = merge_structure_and_resistance(sample_structure, sample_resistance)
        
        assert metrics['total_requested'] == 3
        assert metrics['matches'] == 2  # KEY1 and KEY3
        assert metrics['fraction'] == 2/3

    def test_empty_structure(self, sample_resistance):
        empty_struct = pd.DataFrame(columns=['inchi_key', 'mol_wt'])
        merged, metrics = merge_structure_and_resistance(empty_struct, sample_resistance)
        assert merged.empty
        assert metrics['total_requested'] == 0
        assert metrics['matches'] == 0

    def test_empty_resistance(self, sample_structure):
        empty_res = pd.DataFrame(columns=['inchi_key', 'resistance_score'])
        merged, metrics = merge_structure_and_resistance(sample_structure, empty_res)
        assert len(merged) == 3
        assert all(pd.isna(merged['resistance_score']))
        assert metrics['matches'] == 0
        assert metrics['fraction'] == 0.0
