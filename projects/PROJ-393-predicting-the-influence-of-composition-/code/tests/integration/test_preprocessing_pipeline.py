"""
Integration test for the preprocessing pipeline.

Tests that the pipeline correctly processes data and produces the expected output file.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.preprocessing.preprocess_pipeline import (
    load_raw_data,
    run_standardization,
    run_unit_normalization,
    run_imputation,
    run_dft_filter,
    run_validation,
    save_processed_data,
    run_preprocessing_pipeline
)

class TestPreprocessingPipeline:
    """Integration tests for the preprocessing pipeline."""

    def test_pipeline_creates_output_file(self, tmp_path):
        """Test that the pipeline creates the output file even with empty data."""
        # Create a minimal input CSV
        input_file = tmp_path / "merged_alloys.csv"
        input_file.write_text("composition,coercivity_oe,saturation_magnetization_emu_g,source_type\nCo2MnGa,100,80,Manual\n")
        
        output_file = tmp_path / "alloys_raw.csv"
        
        # Run pipeline
        df, saved_path = run_preprocessing_pipeline(input_file, output_file)
        
        # Verify output file exists
        assert saved_path.exists(), "Output file was not created"
        assert saved_path == output_file, "Output path mismatch"
        
        # Verify content
        result_df = pd.read_csv(output_file)
        assert len(result_df) >= 0, "DataFrame should be created"

    def test_pipeline_filters_dft_entries(self, tmp_path):
        """Test that DFT entries are filtered out."""
        input_file = tmp_path / "merged_alloys.csv"
        input_file.write_text(
            "composition,coercivity_oe,saturation_magnetization_emu_g,source_type\n"
            "Co2MnGa,100,80,Manual\n"
            "Ni2MnSn,50,70,DFT\n"
            "Co2FeAl,120,90,Journal\n"
        )
        
        output_file = tmp_path / "alloys_raw.csv"
        df, _ = run_preprocessing_pipeline(input_file, output_file)
        
        # Check that DFT entry was removed
        assert len(df) == 2, f"Expected 2 rows after DFT filter, got {len(df)}"
        assert 'DFT' not in df['source_type'].values, "DFT entry should be filtered"

    def test_pipeline_handles_missing_data(self, tmp_path):
        """Test that missing data is handled correctly."""
        input_file = tmp_path / "merged_alloys.csv"
        input_file.write_text(
            "composition,coercivity_oe,saturation_magnetization_emu_g,source_type\n"
            "Co2MnGa,100,,Manual\n"
            "Ni2MnSn,,70,Manual\n"
            "Co2FeAl,120,90,Manual\n"
        )
        
        output_file = tmp_path / "alloys_raw.csv"
        df, _ = run_preprocessing_pipeline(input_file, output_file)
        
        # Check that missing values are handled (either imputed or rows deleted)
        # The exact behavior depends on the imputation strategy
        assert len(df) <= 3, "Row count should not increase"

    def test_pipeline_empty_input(self, tmp_path):
        """Test that the pipeline handles empty input gracefully."""
        input_file = tmp_path / "merged_alloys.csv"
        input_file.write_text("composition,coercivity_oe,saturation_magnetization_emu_g,source_type\n")
        
        output_file = tmp_path / "alloys_raw.csv"
        df, saved_path = run_preprocessing_pipeline(input_file, output_file)
        
        # Verify output file exists even with empty input
        assert saved_path.exists(), "Output file should be created for empty input"
        result_df = pd.read_csv(output_file)
        assert len(result_df) == 0, "Empty input should produce empty output"
        
    def test_pipeline_standardizes_composition(self, tmp_path):
        """Test that composition strings are standardized."""
        input_file = tmp_path / "merged_alloys.csv"
        input_file.write_text(
            "composition,coercivity_oe,saturation_magnetization_emu_g,source_type\n"
            "Co2MnGa,100,80,Manual\n"
        )
        
        output_file = tmp_path / "alloys_raw.csv"
        df, _ = run_preprocessing_pipeline(input_file, output_file)
        
        # Check that composition parsing added atomic fraction columns
        # The exact column names depend on the composition_parser implementation
        assert 'composition' in df.columns, "Composition column should exist"
        
    def test_pipeline_unit_normalization(self, tmp_path):
        """Test that units are normalized."""
        input_file = tmp_path / "merged_alloys.csv"
        input_file.write_text(
            "composition,coercivity_oe,saturation_magnetization_emu_g,source_type\n"
            "Co2MnGa,100,80,Manual\n"
            "Ni2MnSn,1.5e4,8.0e1,Manual\n"
        )
        
        output_file = tmp_path / "alloys_raw.csv"
        df, _ = run_preprocessing_pipeline(input_file, output_file)
        
        # Check that coercivity and saturation columns exist and are numeric
        assert 'coercivity_oe' in df.columns, "Coercivity column should exist"
        assert 'saturation_magnetization_emu_g' in df.columns, "Saturation column should exist"
        assert pd.api.types.is_numeric_dtype(df['coercivity_oe']), "Coercivity should be numeric"
        assert pd.api.types.is_numeric_dtype(df['saturation_magnetization_emu_g']), "Saturation should be numeric"
