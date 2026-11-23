"""
Unit tests for the stratify module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile
import json

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.stratify import classify_chemistry, stratify_dataframe, save_stratified_data


class TestClassifyChemistry:
    """Tests for the classify_chemistry function."""

    def test_oxide_classification(self):
        """Test classification of oxide perovskites."""
        assert classify_chemistry("BaTiO3") == "oxide"
        assert classify_chemistry("SrTiO3") == "oxide"
        assert classify_chemistry("LaAlO3") == "oxide"
        assert classify_chemistry("Pb(Zr,Ti)O3") == "oxide" # Complex formula handling

    def test_halide_classification(self):
        """Test classification of halide perovskites."""
        assert classify_chemistry("CsPbI3") == "halide"
        assert classify_chemistry("MAPbBr3") == "halide"
        assert classify_chemistry("CsPbCl3") == "halide"
        assert classify_chemistry("FAPbI3") == "halide"

    def test_nitride_classification(self):
        """Test classification of nitride perovskites."""
        # Note: Real nitride perovskites are rare, but testing the logic
        assert classify_chemistry("SrVN3") == "nitride" # Hypothetical
        assert classify_chemistry("LaFeN3") == "nitride" # Hypothetical

    def test_unknown_classification(self):
        """Test classification of unknown/invalid formulas."""
        assert classify_chemistry("NaCl") == "unknown" # Not ABX3 perovskite structure in this context
        assert classify_chemistry("SiO2") == "unknown"
        assert classify_chemistry("") == "unknown"
        assert classify_chemistry(123) == "unknown" # Invalid type
        assert classify_chemistry("C6H12O6") == "unknown" # Sugar

    def test_case_insensitivity(self):
        """Test that classification is case-insensitive."""
        assert classify_chemistry("batio3") == "oxide"
        assert classify_chemistry("CSPBI3") == "halide"


class TestStratifyDataframe:
    """Tests for the stratify_dataframe function."""

    def test_stratify_success(self):
        """Test successful stratification of a dataframe."""
        data = {
            'structure_id': ['s1', 's2', 's3', 's4'],
            'formula': ['BaTiO3', 'CsPbI3', 'SrTiO3', 'MAPbBr3'],
            'thermal_conductivity': [10.0, 0.5, 12.0, 0.6]
        }
        df = pd.DataFrame(data)
        
        result = stratify_dataframe(df, formula_column='formula')
        
        assert 'chemistry_class' in result.columns
        assert len(result) == len(df)
        assert result.loc[0, 'chemistry_class'] == 'oxide'
        assert result.loc[1, 'chemistry_class'] == 'halide'
        assert result.loc[2, 'chemistry_class'] == 'oxide'
        assert result.loc[3, 'chemistry_class'] == 'halide'

    def test_stratify_missing_column(self):
        """Test that stratification raises error if formula column is missing."""
        data = {
            'structure_id': ['s1', 's2'],
            'thermal_conductivity': [10.0, 0.5]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError):
            stratify_dataframe(df, formula_column='formula')

    def test_stratify_mixed_classes(self):
        """Test stratification with mixed and unknown classes."""
        data = {
            'formula': ['BaTiO3', 'CsPbI3', 'UnknownStuff', 'NaN'],
            'value': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        result = stratify_dataframe(df, formula_column='formula')
        
        assert result.loc[0, 'chemistry_class'] == 'oxide'
        assert result.loc[1, 'chemistry_class'] == 'halide'
        assert result.loc[2, 'chemistry_class'] == 'unknown'
        assert result.loc[3, 'chemistry_class'] == 'unknown' # NaN or empty string


class TestSaveStratifiedData:
    """Tests for the save_stratified_data function."""

    def test_save_to_csv(self):
        """Test saving stratified data to a CSV file."""
        data = {
            'formula': ['BaTiO3', 'CsPbI3'],
            'value': [1, 2]
        }
        df = pd.DataFrame(data)
        df_stratified = stratify_dataframe(df, formula_column='formula')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_stratified.csv"
            save_stratified_data(df_stratified, str(output_path))
            
            assert output_path.exists()
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 2
            assert 'chemistry_class' in loaded_df.columns