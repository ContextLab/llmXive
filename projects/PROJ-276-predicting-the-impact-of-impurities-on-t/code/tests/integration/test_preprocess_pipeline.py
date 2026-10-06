"""
Integration test for the full preprocessing pipeline (T014).
Verifies that T012 and T013 outputs are correctly merged and processed.
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.ingestion.preprocess import preprocess_datasets, main
from code.src.utils.data_provenance import generate_provenance_header


class TestPreprocessPipeline:
    """Integration tests for the preprocessing pipeline."""
    
    def test_full_pipeline_with_mock_data(self):
        """Test the full preprocessing pipeline with mock data from T012 and T013."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create data directories
            raw_dir = tmpdir / "data" / "raw"
            processed_dir = tmpdir / "data" / "processed"
            raw_dir.mkdir(parents=True, exist_ok=True)
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # Create mock Materials Project data (T012 output)
            mp_data = [
                {
                    "material_id": "mp-1",
                    "tc": 39.0,
                    "impurity_c_weight": 1.0,
                    "impurity_o_weight": 0.5,
                    "temp_k": 300.0,
                    "pressure_gpa": 0.0
                },
                {
                    "material_id": "mp-2",
                    "tc": 38.5,
                    "impurity_c_weight": 2.0,
                    "impurity_o_weight": 1.0,
                    "temp_k": 350.0,
                    "pressure_gpa": 0.0
                },
                {
                    "material_id": "mp-3",
                    "tc": np.nan,  # Should be filtered out
                    "impurity_c_weight": 1.5,
                    "impurity_o_weight": 0.8,
                    "temp_k": 400.0,
                    "pressure_gpa": 0.0
                }
            ]
            
            mp_file = raw_dir / "materials_project_mgb2.json"
            with open(mp_file, 'w') as f:
                json.dump(mp_data, f)
            
            # Create mock SuperCon data (T013 output)
            supercon_data = {
                "tc": [38.0, 37.5, 37.0],
                "impurity_c_weight": [0.5, 1.5, 2.5],
                "impurity_o_weight": [0.2, 0.8, 1.2],
                "temp_k": [300.0, 320.0, 340.0],
                "pressure_gpa": [0.0, 0.0, 0.0]
            }
            
            supercon_file = raw_dir / "supercon_mgb2.csv"
            pd.DataFrame(supercon_data).to_csv(supercon_file, index=False)
            
            # Temporarily override paths
            import code.src.ingestion.preprocess as preprocess_module
            original_mp_file = preprocess_module.MATERIALS_PROJECT_FILE
            original_supercon_file = preprocess_module.SUPERCON_FILE
            original_processed_dir = preprocess_module.DATA_PROCESSED_DIR
            original_raw_dir = preprocess_module.DATA_RAW_DIR
            
            preprocess_module.DATA_RAW_DIR = raw_dir
            preprocess_module.DATA_PROCESSED_DIR = processed_dir
            preprocess_module.MATERIALS_PROJECT_FILE = mp_file
            preprocess_module.SUPERCON_FILE = supercon_file
            
            try:
                # Run preprocessing
                result_df = preprocess_datasets()
                
                # Verify output
                assert len(result_df) == 5, f"Expected 5 rows (2 MP + 3 SuperCon, 1 MP filtered), got {len(result_df)}"
                assert "Tc" in result_df.columns
                assert "impurity_C" in result_df.columns or "impurity_C_atomic" in result_df.columns
                assert "source" in result_df.columns
                assert all(result_df["Tc"].notna()), "All Tc values should be non-null"
                assert all(result_df["source"].isin(["materials_project", "supercon"]))
                
                # Check provenance
                assert "provenance" in result_df.attrs
                assert "provenance_header" in result_df.attrs
                assert len(result_df.attrs["provenance"]["sources"]) == 2
                
                # Verify output file was created
                output_file = processed_dir / "mgb2_clean.csv"
                assert output_file.exists(), f"Output file not created: {output_file}"
                
                # Verify file content
                with open(output_file, 'r') as f:
                    content = f.read()
                    assert "# PROVENANCE:" in content
                    
                # Load and verify CSV
                loaded_df = pd.read_csv(output_file)
                assert len(loaded_df) == len(result_df)
                assert list(loaded_df.columns) == list(result_df.columns)
                
            finally:
                # Restore original paths
                preprocess_module.MATERIALS_PROJECT_FILE = original_mp_file
                preprocess_module.SUPERCON_FILE = original_supercon_file
                preprocess_module.DATA_PROCESSED_DIR = original_processed_dir
                preprocess_module.DATA_RAW_DIR = original_raw_dir
    
    def test_pipeline_with_synthesis_ranges(self):
        """Test handling of synthesis ranges in input data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            raw_dir = tmpdir / "data" / "raw"
            processed_dir = tmpdir / "data" / "processed"
            raw_dir.mkdir(parents=True, exist_ok=True)
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # Create data with synthesis ranges
            mp_data = [
                {
                    "material_id": "mp-1",
                    "tc": "300-400",  # Range that should be converted to midpoint
                    "impurity_c_weight": 1.0,
                    "impurity_o_weight": 0.5,
                    "temp_k": 300.0,
                    "pressure_gpa": 0.0
                }
            ]
            
            mp_file = raw_dir / "materials_project_mgb2.json"
            with open(mp_file, 'w') as f:
                json.dump(mp_data, f)
            
            supercon_file = raw_dir / "supercon_mgb2.csv"
            pd.DataFrame({
                "tc": [38.0],
                "impurity_c_weight": [0.5],
                "impurity_o_weight": [0.2],
                "temp_k": [300.0],
                "pressure_gpa": [0.0]
            }).to_csv(supercon_file, index=False)
            
            import code.src.ingestion.preprocess as preprocess_module
            original_mp_file = preprocess_module.MATERIALS_PROJECT_FILE
            original_supercon_file = preprocess_module.SUPERCON_FILE
            preprocess_module.DATA_RAW_DIR = raw_dir
            preprocess_module.DATA_PROCESSED_DIR = processed_dir
            preprocess_module.MATERIALS_PROJECT_FILE = mp_file
            preprocess_module.SUPERCON_FILE = supercon_file
            
            try:
                result_df = preprocess_datasets()
                
                # Tc should be converted to midpoint (350.0)
                assert result_df["Tc"].iloc[0] == 350.0
            finally:
                preprocess_module.MATERIALS_PROJECT_FILE = original_mp_file
                preprocess_module.SUPERCON_FILE = original_supercon_file
    
    def test_pipeline_empty_impurities(self):
        """Test that entries with all missing impurities are filtered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            raw_dir = tmpdir / "data" / "raw"
            processed_dir = tmpdir / "data" / "processed"
            raw_dir.mkdir(parents=True, exist_ok=True)
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            mp_data = [
                {
                    "material_id": "mp-1",
                    "tc": 39.0,
                    "impurity_c_weight": np.nan,
                    "impurity_o_weight": np.nan
                }
            ]
            
            mp_file = raw_dir / "materials_project_mgb2.json"
            with open(mp_file, 'w') as f:
                json.dump(mp_data, f)
            
            supercon_file = raw_dir / "supercon_mgb2.csv"
            pd.DataFrame({
                "tc": [38.0],
                "impurity_c_weight": [0.5],
                "impurity_o_weight": [0.2]
            }).to_csv(supercon_file, index=False)
            
            import code.src.ingestion.preprocess as preprocess_module
            original_mp_file = preprocess_module.MATERIALS_PROJECT_FILE
            original_supercon_file = preprocess_module.SUPERCON_FILE
            preprocess_module.DATA_RAW_DIR = raw_dir
            preprocess_module.DATA_PROCESSED_DIR = processed_dir
            preprocess_module.MATERIALS_PROJECT_FILE = mp_file
            preprocess_module.SUPERCON_FILE = supercon_file
            
            try:
                result_df = preprocess_datasets()
                
                # The entry with all NaN impurities should be filtered out
                assert len(result_df) == 1
                assert result_df.iloc[0]["source"] == "supercon"
            finally:
                preprocess_module.MATERIALS_PROJECT_FILE = original_mp_file
                preprocess_module.SUPERCON_FILE = original_supercon_file