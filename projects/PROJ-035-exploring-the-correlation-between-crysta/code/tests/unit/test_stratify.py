import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import sys
import os

# Add code directory to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.analysis.stratify import classify_chemistry, stratify_dataframe, save_stratified_data, main

class TestClassifyChemistry:
    def test_oxide_classification(self):
        assert classify_chemistry("CaTiO3") == "oxide"
        assert classify_chemistry("BaTiO3") == "oxide"
        assert classify_chemistry("SrTiO3") == "oxide"
    
    def test_halide_classification(self):
        assert classify_chemistry("CsPbI3") == "halide"
        assert classify_chemistry("MAPbCl3") == "halide"
        assert classify_chemistry("FAPbBr3") == "halide"
    
    def test_nitride_classification(self):
        assert classify_chemistry("Sr3N2") == "nitride" # Hypothetical perovskite-like
        # Real nitride perovskites are rare but the logic holds for 'N' presence without 'O' or halogens
        assert classify_chemistry("Ca3N2") == "nitride"
    
    def test_unknown_classification(self):
        assert classify_chemistry("SiO2") == "unknown" # Not ABX3, but logic checks elements
        # Actually SiO2 has O, so it would be oxide by simple logic. 
        # Let's test empty/invalid
        assert classify_chemistry("") == "unknown"
        assert classify_chemistry(np.nan) == "unknown"
        assert classify_chemistry(None) == "unknown"

class TestStratifyDataFrame:
    def test_stratify_success(self):
        data = {
            'id': [1, 2, 3, 4],
            'chemistry_class': ['oxide', 'halide', 'oxide', 'nitride'],
            'value': [10, 20, 30, 40]
        }
        df = pd.DataFrame(data)
        result = stratify_dataframe(df, 'chemistry_class')
        
        assert 'oxide' in result
        assert 'halide' in result
        assert 'nitride' in result
        assert len(result['oxide']) == 2
        assert len(result['halide']) == 1
        assert len(result['nitride']) == 1
    
    def test_stratify_missing_column(self):
        data = {'id': [1, 2]}
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            stratify_dataframe(df, 'non_existent_column')
    
    def test_stratify_empty_result(self):
        data = {
            'id': [1, 2],
            'chemistry_class': ['unknown', 'unknown']
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            stratify_dataframe(df, 'chemistry_class')

class TestSaveStratifiedData:
    def test_save_stratified_data(self):
        data = {
            'id': [1, 2, 3],
            'chemistry_class': ['oxide', 'halide', 'oxide'],
            'value': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        stratified = stratify_dataframe(df, 'chemistry_class')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            files = save_stratified_data(stratified, tmpdir, seed=42)
            
            assert len(files) == 2 # oxide and halide
            for f in files:
                assert Path(f).exists()
                assert f.endswith('.csv')
                
                # Verify content
                df_read = pd.read_csv(f)
                assert not df_read.empty

class TestIntegration:
    def test_full_stratify_workflow(self):
        # Create a mock dataset
        data = {
            'structure_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
            'thermal_conductivity': [10.0, 20.0, 30.0, 40.0, 50.0],
            'chemistry_class': ['oxide', 'halide', 'oxide', 'nitride', 'halide'],
            'tolerance_factor': [0.9, 0.8, 0.95, 0.85, 0.92]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.csv"
            df.to_csv(input_file, index=False)
            
            output_dir = Path(tmpdir) / "output"
            
            # Simulate main execution
            sys.argv = ['stratify.py', '--input', str(input_file), '--output', str(output_dir), '--seed', '42']
            try:
                main()
            except SystemExit:
                pass # Expected after successful run
            
            assert output_dir.exists()
            oxide_file = output_dir / "stratified_oxide.csv"
            halide_file = output_dir / "stratified_halide.csv"
            nitride_file = output_dir / "stratified_nitride.csv"
            
            assert oxide_file.exists()
            assert halide_file.exists()
            assert nitride_file.exists()
            
            oxide_df = pd.read_csv(oxide_file)
            assert len(oxide_df) == 2
            assert all(oxide_df['chemistry_class'] == 'oxide')