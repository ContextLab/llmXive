import pytest
import pandas as pd
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add code directory to path for imports
code_dir = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(code_dir))

from data.scaling_metric_setup import load_enriched_data, add_complexity_metric, save_enriched_data

class TestScalingMetricSetup:
    
    @pytest.fixture
    def temp_enriched_csv(self, tmp_path):
        """Create a temporary enriched_data.csv file with mock data."""
        data = {
            'smiles': ['CCO', 'CCO', 'CCO'],
            'logPapp': [-5.0, -6.0, -7.0],
            'mw': [46.0, 46.0, 46.0],
            'psa': [20.0, 20.0, 20.0],
            'logP': [-0.5, -0.6, -0.7],
            'assay_id': ['A1', 'A2', 'A3'],
            'protocol_metadata': ['{"standard_type": "MEASUREMENT"}'] * 3
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "enriched_data.csv"
        df.to_csv(file_path, index=False)
        return file_path

    def test_load_enriched_data(self, temp_enriched_csv):
        """Test that load_enriched_data correctly reads the CSV."""
        df = load_enriched_data(temp_enriched_csv)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert 'mw' in df.columns
        assert 'smiles' in df.columns

    def test_load_enriched_data_missing_file(self):
        """Test that FileNotFoundError is raised for missing input."""
        with pytest.raises(FileNotFoundError):
            load_enriched_data(Path("/nonexistent/path/file.csv"))

    def test_load_enriched_data_missing_mw(self, tmp_path):
        """Test that ValueError is raised if 'mw' column is missing."""
        data = {
            'smiles': ['CCO'],
            'logPapp': [-5.0]
        }
        df = pd.DataFrame(data)
        file_path = tmp_path / "bad_data.csv"
        df.to_csv(file_path, index=False)
        
        with pytest.raises(ValueError, match="Required column 'mw' not found"):
            load_enriched_data(file_path)

    def test_add_complexity_metric(self, temp_enriched_csv):
        """Test that add_complexity_metric creates a copy of 'mw'."""
        df = load_enriched_data(temp_enriched_csv)
        df_result = add_complexity_metric(df)
        
        assert 'complexity_metric' in df_result.columns
        assert df_result['complexity_metric'].equals(df_result['mw'])
        assert len(df_result) == len(df)

    def test_save_enriched_data(self, temp_enriched_csv, tmp_path):
        """Test that save_enriched_data writes the file correctly."""
        df = load_enriched_data(temp_enriched_csv)
        df_processed = add_complexity_metric(df)
        
        output_path = tmp_path / "output_enriched.csv"
        save_enriched_data(df_processed, output_path)
        
        assert output_path.exists()
        
        # Verify content
        df_loaded = pd.read_csv(output_path)
        assert 'complexity_metric' in df_loaded.columns
        assert len(df_loaded) == 3