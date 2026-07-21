import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.preprocessing.preprocess_pipeline import (
    load_raw_data,
    run_standardization,
    run_unit_normalization,
    run_imputation,
    run_dft_filter,
    run_validation,
    run_preprocessing_pipeline
)

class TestPreprocessingPipeline:
    @pytest.fixture
    def sample_raw_data(self):
        data = {
            "composition": ["Co2MnGa", "Fe3Ga", "Ni2MnGa", "DFT_Co2MnGa", "Co2FeAl"],
            "coercivity_oe": [100.0, 50.0, 200.0, 150.0, None],
            "saturation_magnetization_emu_g": [120.0, 150.0, 90.0, 110.0, 80.0],
            "source_type": ["Manual", "Journal", "Manual", "DFT", "Journal"]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_input_dir(self, sample_raw_data):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            file_path = input_dir / "merged_raw_data.csv"
            sample_raw_data.to_csv(file_path, index=False)
            yield input_dir

    @pytest.fixture
    def temp_output_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_load_raw_data(self, temp_input_dir):
        df = load_raw_data(temp_input_dir)
        assert not df.empty
        assert "composition" in df.columns

    def test_run_dft_filter(self, sample_raw_data):
        # Simulate a DataFrame with a DFT entry
        filtered = run_dft_filter(sample_raw_data)
        # Should remove the row where composition starts with DFT or source_type is DFT
        # In our sample, "DFT_Co2MnGa" and "DFT" source should be removed
        assert len(filtered) < len(sample_raw_data)
        assert not filtered[filtered["composition"].str.contains("DFT")].empty == False

    def test_run_imputation(self, sample_raw_data):
        # Run imputation on data with a missing value
        imputed = run_imputation(sample_raw_data)
        # Check that missing values are filled (mean imputation)
        assert imputed["coercivity_oe"].isna().sum() == 0

    def test_full_pipeline(self, temp_input_dir, temp_output_dir):
        output_file = temp_output_dir / "alloys_raw.csv"
        run_preprocessing_pipeline(input_dir=temp_input_dir, output_dir=temp_output_dir)
        
        assert output_file.exists()
        result_df = pd.read_csv(output_file)
        assert not result_df.empty
        # Verify DFT entries are removed
        assert not result_df[result_df["composition"].str.contains("DFT")].empty == False
        # Verify missing values are imputed
        assert result_df["coercivity_oe"].isna().sum() == 0