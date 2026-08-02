import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys
import json

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.preprocessing.preprocess_pipeline import load_raw_data, run_preprocessing_pipeline
from src.preprocessing.imputation_orchestrator import orchestrate_imputation
from src.preprocessing.dft_filter import filter_dft_entries

class TestPreprocessingPipeline:
    
    def test_pipeline_produces_output_file(self, tmp_path):
        """
        T027 Test: Ensure the pipeline produces data/processed/alloys_raw.csv.
        Even if the input data is empty or small, the file must be created.
        """
        # We mock the data loading to ensure we have some data to process
        # In a real integration test, we might rely on existing data files.
        # Here we simulate the flow.
        
        # Create a mock DataFrame
        mock_data = pd.DataFrame({
            'composition': ['Co2MnGa', 'NiMnSn'],
            'coercivity_oe': [100.0, 150.0],
            'saturation_magnetization_emu_g': [80.0, 70.0],
            'source_type': ['Manual', 'Manual']
        })
        
        # Patch load_raw_data to return our mock data
        import src.preprocessing.preprocess_pipeline as pp_module
        original_load = pp_module.load_raw_data
        pp_module.load_raw_data = lambda: mock_data
        
        try:
            # Temporarily redirect output path
            original_output_dir = pp_module.DATA_PROCESSED_DIR
            pp_module.DATA_PROCESSED_DIR = tmp_path
            
            result = run_preprocessing_pipeline()
            
            output_file = tmp_path / "alloys_raw.csv"
            assert output_file.exists(), "Output file alloys_raw.csv was not created."
            
            # Verify content
            result_df = pd.read_csv(output_file)
            assert len(result_df) > 0, "Output file is empty."
            assert 'composition' in result_df.columns
            assert 'coercivity_oe' in result_df.columns
            
        finally:
            # Restore
            pp_module.load_raw_data = original_load
            pp_module.DATA_PROCESSED_DIR = original_output_dir

    def test_imputation_logic_switches_at_15_percent(self):
        """
        T015 Integration Test: Validates Spec FR-002.
        Tests that mean imputation is used for <=15% missing, and listwise for >15%.
        """
        # Case 1: 14% missing (Mean Imputation)
        df_low_missing = pd.DataFrame({
            'A': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 
                  11.0, 12.0, 13.0, 14.0, None] # 1/15 = 6.6% missing
        })
        # Actually let's make it exactly 14%: 14 rows, 2 missing -> 14.2%
        # 100 rows, 14 missing -> 14%
        rows = 100
        missing_count = 14
        data = list(range(rows - missing_count)) + [None] * missing_count
        df_low_missing = pd.DataFrame({'val': data})
        
        result_low = orchestrate_imputation(df_low_missing)
        # With mean imputation, no rows should be dropped
        assert len(result_low) == len(df_low_missing), "Mean imputation should not drop rows."
        
        # Case 2: 16% missing (Listwise Deletion)
        # 100 rows, 16 missing -> 16%
        missing_count_high = 16
        data_high = list(range(rows - missing_count_high)) + [None] * missing_count_high
        df_high_missing = pd.DataFrame({'val': data_high})
        
        result_high = orchestrate_imputation(df_high_missing)
        # With listwise deletion, rows with missing values are dropped
        assert len(result_high) < len(df_high_missing), "Listwise deletion should drop rows with missing values."
        assert len(result_high) == rows - missing_count_high

    def test_dft_filter_excludes_dft_entries(self):
        """
        T014 Integration Test: Ensures DFT targets are excluded.
        """
        df = pd.DataFrame({
            'composition': ['Co2MnGa', 'NiMnSn', 'Fe3Al'],
            'coercivity_oe': [100, 150, 200],
            'source_type': ['NIST', 'Journal', 'DFT_Calculated'],
            'target_source': [None, None, 'Materials Project']
        })
        
        filtered = filter_dft_entries(df)
        
        assert len(filtered) == 2, "DFT entries should be filtered out."
        assert 'DFT_Calculated' not in filtered['source_type'].values
        assert 'Materials Project' not in filtered['target_source'].values if 'target_source' in filtered.columns else True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])