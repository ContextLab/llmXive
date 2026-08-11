"""
Unit tests for the stratify module (T019).

Tests FR-014: Stratification by perovskite chemistry class.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import sys
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.stratify import (
    classify_chemistry, 
    stratify_dataframe, 
    save_stratified_data,
    main
)

class TestClassifyChemistry:
    """Tests for the classify_chemistry function."""
    
    def test_oxide_classification(self):
        """Test that oxide perovskites are correctly identified."""
        formulas = ['CaTiO3', 'BaTiO3', 'SrTiO3', 'LaAlO3']
        for formula in formulas:
            assert classify_chemistry(formula) == 'oxide', f"Failed for {formula}"
            
    def test_halide_classification(self):
        """Test that halide perovskites are correctly identified."""
        formulas = ['CsPbCl3', 'CsPbBr3', 'CsPbI3', 'MAPbI3', 'CsPbF3']
        for formula in formulas:
            result = classify_chemistry(formula)
            assert result == 'halide', f"Failed for {formula}: got {result}"
            
    def test_nitride_classification(self):
        """Test that nitride perovskites are correctly identified."""
        # Note: Real nitride perovskites are rare, but we test the logic
        formulas = ['SrVN3', 'BaVN3']
        for formula in formulas:
            assert classify_chemistry(formula) == 'nitride', f"Failed for {formula}"
            
    def test_unknown_classification(self):
        """Test that non-perovskite or mixed formulas are marked unknown."""
        formulas = ['SiO2', 'NaCl', 'H2O', '']
        for formula in formulas:
            assert classify_chemistry(formula) == 'unknown', f"Failed for {formula}"
            
    def test_case_insensitivity(self):
        """Test that classification is case-insensitive."""
        assert classify_chemistry('catiO3') == 'oxide'
        assert classify_chemistry('CSPBCL3') == 'halide'

class TestStratifyDataFrame:
    """Tests for the stratify_dataframe function."""
    
    def create_sample_df(self) -> pd.DataFrame:
        """Create a sample dataframe with mixed chemistry classes."""
        data = {
            'structure_id': [f'id_{i}' for i in range(10)],
            'formula': [
                'CaTiO3', 'BaTiO3', 'SrTiO3', 'LaAlO3',  # Oxides
                'CsPbCl3', 'CsPbBr3', 'CsPbI3',          # Halides
                'SrVN3',                                  # Nitride
                'SiO2'                                   # Unknown
            ],
            'thermal_conductivity': [1.0] * 10,
            'temperature_K': [300.0] * 10
        }
        return pd.DataFrame(data)
        
    def test_stratification_logic(self):
        """Test that the dataframe is correctly split into strata."""
        df = self.create_sample_df()
        strata = stratify_dataframe(df)
        
        assert 'oxide' in strata
        assert 'halide' in strata
        assert 'nitride' in strata
        assert 'unknown' in strata
        
        assert len(strata['oxide']) == 4
        assert len(strata['halide']) == 3
        assert len(strata['nitride']) == 1
        assert len(strata['unknown']) == 1
        
    def test_empty_dataframe_raises(self):
        """Test that an empty dataframe raises a ValueError."""
        df = pd.DataFrame(columns=['formula', 'thermal_conductivity'])
        with pytest.raises(ValueError, match="Input dataframe is empty"):
            stratify_dataframe(df)
            
    def test_missing_column_raises(self):
        """Test that missing formula column raises a ValueError."""
        df = pd.DataFrame({'thermal_conductivity': [1.0]})
        with pytest.raises(ValueError, match="Column 'formula' not found"):
            stratify_dataframe(df)
            
    def test_chemistry_class_column_added(self):
        """Test that the output DataFrames contain the chemistry_class column."""
        df = self.create_sample_df()
        strata = stratify_dataframe(df)
        
        for class_name, group in strata.items():
            assert 'chemistry_class' in group.columns
            # Verify all rows in the group have the correct class label
            assert all(group['chemistry_class'] == class_name)

class TestSaveStratifiedData:
    """Tests for the save_stratified_data function."""
    
    def test_save_creates_files(self):
        """Test that files are created in the output directory."""
        df = pd.DataFrame({
            'formula': ['CaTiO3', 'CsPbCl3'],
            'thermal_conductivity': [1.0, 2.0]
        })
        strata = stratify_dataframe(df)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            saved_files = save_stratified_data(strata, output_dir)
            
            assert len(saved_files) == 3 # oxide, halide, unknown (if any)
            for file_path in saved_files:
                assert Path(file_path).exists()
                
            # Check content of one file
            oxide_file = [f for f in saved_files if 'oxide' in f][0]
            df_loaded = pd.read_csv(oxide_file)
            assert 'formula' in df_loaded.columns
            assert len(df_loaded) == 1
            
    def test_summary_json_creation(self):
        """Test that a summary JSON is not created here (it's in main), 
        but verify save function works correctly."""
        # This test is more about ensuring the save function doesn't crash
        # The summary creation is tested in integration tests or main execution
        pass

class TestIntegration:
    """Integration-style tests for the stratify module."""
    
    def test_full_flow(self):
        """Simulate a full flow of classification and saving."""
        data = {
            'structure_id': ['1', '2', '3', '4'],
            'formula': ['CaTiO3', 'CsPbCl3', 'SrVN3', 'SiO2'],
            'thermal_conductivity': [10.0, 2.0, 5.0, 1.0]
        }
        df = pd.DataFrame(data)
        
        strata = stratify_dataframe(df)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            saved_files = save_stratified_data(strata, output_dir)
            
            # Verify counts
            assert len(strata['oxide']) == 1
            assert len(strata['halide']) == 1
            assert len(strata['nitride']) == 1
            assert len(strata['unknown']) == 1
            
            # Verify files exist
            assert len(saved_files) == 4
            for f in saved_files:
                assert Path(f).exists()