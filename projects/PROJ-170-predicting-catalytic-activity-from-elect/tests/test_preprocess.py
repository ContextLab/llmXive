import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "code"))

from preprocess import (
    parse_oc20_to_dataframe,
    construct_unified_dataframe,
    retrieve_target_variable,
    compute_stoichiometry_features,
    define_global_vocabulary_and_zero_pad
)
from config import get_project_root

class TestT016cVocabulary:
    """Tests for T016c: Define Global Vocabulary & Zero-Padding"""

    def setup_method(self):
        """Create a minimal test DataFrame"""
        self.test_df = pd.DataFrame({
            'composition': ['Fe2O3', 'Pt', 'CuO'],
            'surface_facet': ['111', '100', '001'],
            'experimental_tof': [1.0, 2.0, 3.0],
            'd_band_center': [-1.0, -2.0, -3.0],
            'adsorption_energy': [-0.5, -1.0, -1.5]
        })

    def test_vocabulary_creation(self):
        """Test that vocabulary is created correctly"""
        df = self.test_df.copy()
        df, elements = compute_stoichiometry_features(df)
        
        vocab = define_global_vocabulary_and_zero_pad(df, elements)
        
        # Check that vocabulary contains all expected elements
        expected_elements = {'Fe', 'O', 'Pt', 'Cu'}
        assert set(vocab.keys()) == expected_elements
        
        # Check that vocabulary is a mapping of element to index
        for elem, idx in vocab.items():
            assert isinstance(elem, str)
            assert isinstance(idx, int)
            assert idx >= 0

    def test_zero_padding(self):
        """Test that stoichiometry vectors are zero-padded for missing elements"""
        df = self.test_df.copy()
        df, elements = compute_stoichiometry_features(df)
        
        # Check that all stoich columns exist
        stoich_cols = [c for c in df.columns if c.startswith('stoich_')]
        assert len(stoich_cols) == len(elements)
        
        # Check that Fe2O3 has non-zero Fe and O, but zero Pt and Cu
        fe2o3_row = df[df['composition'] == 'Fe2O3'].iloc[0]
        assert fe2o3_row['stoich_Fe'] > 0
        assert fe2o3_row['stoich_O'] > 0
        assert fe2o3_row['stoich_Pt'] == 0.0
        assert fe2o3_row['stoich_Cu'] == 0.0

    def test_vocabulary_file_created(self):
        """Test that vocabulary file is saved to correct location"""
        df = self.test_df.copy()
        df, elements = compute_stoichiometry_features(df)
        
        vocab = define_global_vocabulary_and_zero_pad(df, elements)
        
        vocab_path = get_project_root() / "data" / "processed" / "stoich_vocab.json"
        assert vocab_path.exists(), f"Vocabulary file not created at {vocab_path}"
        
        # Verify file content
        with open(vocab_path, 'r') as f:
            saved_vocab = json.load(f)
        
        assert saved_vocab == vocab

    def test_fixed_dimensionality(self):
        """Test that all rows have the same number of stoichiometry columns"""
        df = self.test_df.copy()
        df, elements = compute_stoichiometry_features(df)
        
        stoich_cols = [c for c in df.columns if c.startswith('stoich_')]
        
        # All rows should have the same columns
        for idx, row in df.iterrows():
            assert len([c for c in stoich_cols if not pd.isna(row[c])]) == len(stoich_cols)

    def test_vocabulary_order_consistency(self):
        """Test that vocabulary order is consistent (sorted)"""
        df = self.test_df.copy()
        df, elements = compute_stoichiometry_features(df)
        
        vocab = define_global_vocabulary_and_zero_pad(df, elements)
        
        # Elements should be sorted
        assert elements == sorted(elements)
        
        # Vocabulary indices should match sorted order
        for idx, elem in enumerate(elements):
            assert vocab[elem] == idx