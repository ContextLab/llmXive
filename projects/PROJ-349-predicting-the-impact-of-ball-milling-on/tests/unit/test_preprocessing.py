"""
Unit tests for preprocessing pipeline.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest

from src.preprocess.pipeline import (
    run_preprocessing_pipeline,
    calculate_process_duration,
    _extract_process_duration,
    _parse_time_to_hours,
    _flag_unstructured_entries
)
from src.exceptions import DataFormatError, SchemaValidationError


class TestParseTimeToHours:
    def test_parse_hours_with_h(self):
        assert _parse_time_to_hours("2.5h") == 2.5
        assert _parse_time_to_hours("3h") == 3.0
    
    def test_parse_hours_with_hr(self):
        assert _parse_time_to_hours("4hr") == 4.0
        assert _parse_time_to_hours("1.5hr") == 1.5
    
    def test_parse_hours_with_hours(self):
        assert _parse_time_to_hours("2 hours") == 2.0
        assert _parse_time_to_hours("0.5hours") == 0.5
    
    def test_parse_minutes(self):
        assert _parse_time_to_hours("30min") == 0.5
        assert _parse_time_to_hours("90minutes") == 1.5
    
    def test_parse_invalid(self):
        assert _parse_time_to_hours("invalid") is None
        assert _parse_time_to_hours("") is None
        assert _parse_time_to_hours(None) is None
        assert _parse_time_to_hours(123) is None


class TestExtractProcessDuration:
    def test_extract_from_existing_column(self):
        row = pd.Series({
            'process_duration': 5.0,
            'end_time': '2023-01-01',
            'start_time': '2023-01-01',
            'raw_text_logs': 'milling_time: 10h'
        })
        assert _extract_process_duration(row) == 5.0
    
    def test_extract_from_timestamps(self):
        row = pd.Series({
            'process_duration': np.nan,
            'end_time': '2023-01-01 10:00:00',
            'start_time': '2023-01-01 08:00:00',
            'raw_text_logs': 'milling_time: 10h'
        })
        assert _extract_process_duration(row) == 2.0  # 2 hours
    
    def test_extract_from_raw_text(self):
        row = pd.Series({
            'process_duration': np.nan,
            'raw_text_logs': 'Experiment ran for 3.5 hours milling'
        })
        assert _extract_process_duration(row) == 3.5
    
    def test_extract_fallback_to_none(self):
        row = pd.Series({
            'process_duration': np.nan,
            'raw_text_logs': 'No time information here'
        })
        assert _extract_process_duration(row) is None


class TestCalculateProcessDuration:
    def test_calculate_with_missing_values(self):
        df = pd.DataFrame({
            'process_duration': [1.0, np.nan, np.nan, 4.0],
            'end_time': ['2023-01-01 10:00', '2023-01-01 12:00', '2023-01-01 14:00', '2023-01-01 16:00'],
            'start_time': ['2023-01-01 08:00', '2023-01-01 10:00', '2023-01-01 12:00', '2023-01-01 14:00']
        })
        
        result = calculate_process_duration(df)
        
        # First and last should remain unchanged
        assert result.loc[0, 'process_duration'] == 1.0
        assert result.loc[3, 'process_duration'] == 4.0
        
        # Middle two should be derived (2 hours each)
        assert result.loc[1, 'process_duration'] == 2.0
        assert result.loc[2, 'process_duration'] == 2.0
    
    def test_calculate_with_raw_text_fallback(self):
        df = pd.DataFrame({
            'process_duration': [np.nan, np.nan],
            'raw_text_logs': ['milling_time: 5h', 'duration: 3 hours']
        })
        
        result = calculate_process_duration(df)
        
        assert result.loc[0, 'process_duration'] == 5.0
        assert result.loc[1, 'process_duration'] == 3.0


class TestFlagUnstructuredEntries:
    def test_flag_image_path_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'flagged.json'
            
            df = pd.DataFrame({
                'experiment_id': ['exp1', 'exp2', 'exp3'],
                'source': ['src1', 'src2', 'src3'],
                'psd_image_path': ['path/to/img1.png', None, 'path/to/img2.png']
            })
            
            _flag_unstructured_entries(df, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                flagged = json.load(f)
            
            assert len(flagged) == 2
            assert flagged[0]['experiment_id'] == 'exp1'
            assert flagged[1]['experiment_id'] == 'exp3'
    
    def test_flag_has_psd_image_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'flagged.json'
            
            df = pd.DataFrame({
                'experiment_id': ['exp1', 'exp2', 'exp3'],
                'source': ['src1', 'src2', 'src3'],
                'has_psd_image': [True, False, True]
            })
            
            _flag_unstructured_entries(df, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                flagged = json.load(f)
            
            assert len(flagged) == 2


class TestRunPreprocessingPipeline:
    def test_basic_pipeline(self):
        df = pd.DataFrame({
            'experiment_id': ['exp1', 'exp2', 'exp3'],
            'material_type': ['ceramic', 'metal', 'polymer'],
            'ball_milling_speed': [100, 200, np.nan],
            'ball_to_powder_ratio': [10, 15, 20],
            'D50': [5.0, 10.0, 15.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'processed.parquet'
            flagged_path = Path(tmpdir) / 'flagged.json'
            
            processed_df, metadata = run_preprocessing_pipeline(
                input_df=df,
                output_path=output_path,
                flagged_output_path=flagged_path
            )
            
            # Check output
            assert len(processed_df) == 3
            assert 'D50' in processed_df.columns
            assert 'experiment_id' in processed_df.columns
            
            # Check metadata
            assert metadata['input_rows'] == 3
            assert metadata['output_rows'] == 3
            assert 'material_type' in metadata['categorical_features_processed']
            assert 'ball_milling_speed' in metadata['numeric_features_processed']
    
    def test_empty_input_raises_error(self):
        df = pd.DataFrame()
        
        with pytest.raises(DataFormatError):
            run_preprocessing_pipeline(df)
    
    def test_no_predictors_raises_error(self):
        df = pd.DataFrame({
            'experiment_id': ['exp1'],
            'D50': [5.0]
        })
        
        with pytest.raises(SchemaValidationError):
            run_preprocessing_pipeline(df)
    
    def test_imputation_works(self):
        df = pd.DataFrame({
            'material_type': ['ceramic', 'metal', 'polymer'],
            'ball_milling_speed': [100, np.nan, 300],
            'ball_to_powder_ratio': [10, 15, 20],
            'D50': [5.0, 10.0, 15.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'processed.parquet'
            
            processed_df, _ = run_preprocessing_pipeline(
                input_df=df,
                output_path=output_path
            )
            
            # Check that imputation happened (no NaN in numeric features)
            numeric_cols = [c for c in processed_df.columns if c.startswith('ball_milling_speed') or c.startswith('ball_to_powder_ratio')]
            assert not processed_df[numeric_cols].isna().any().any()
    
    def test_scaling_applied(self):
        df = pd.DataFrame({
            'material_type': ['ceramic', 'metal', 'polymer'],
            'ball_milling_speed': [100, 200, 300],
            'ball_to_powder_ratio': [10, 20, 30],
            'D50': [5.0, 10.0, 15.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'processed.parquet'
            
            processed_df, _ = run_preprocessing_pipeline(
                input_df=df,
                output_path=output_path
            )
            
            # Check that scaled features have mean ~0 and std ~1
            numeric_cols = [c for c in processed_df.columns if c not in ['D50', 'experiment_id']]
            for col in numeric_cols:
                col_data = processed_df[col]
                # Allow some tolerance for floating point
                assert abs(col_data.mean()) < 0.1, f"Mean of {col} should be ~0"
                assert abs(col_data.std() - 1.0) < 0.1, f"Std of {col} should be ~1"
    
    def test_one_hot_encoding(self):
        df = pd.DataFrame({
            'material_type': ['ceramic', 'metal', 'polymer'],
            'ball_milling_speed': [100, 200, 300],
            'D50': [5.0, 10.0, 15.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'processed.parquet'
            
            processed_df, metadata = run_preprocessing_pipeline(
                input_df=df,
                output_path=output_path
            )
            
            # Check that one-hot encoded columns exist
            assert any('material_type_ceramic' in c for c in processed_df.columns)
            assert any('material_type_metal' in c for c in processed_df.columns)
            assert any('material_type_polymer' in c for c in processed_df.columns)
    
    def test_process_duration_calculation(self):
        df = pd.DataFrame({
            'material_type': ['ceramic', 'metal', 'polymer'],
            'ball_milling_speed': [100, 200, 300],
            'end_time': ['2023-01-01 10:00', '2023-01-01 12:00', '2023-01-01 14:00'],
            'start_time': ['2023-01-01 08:00', '2023-01-01 10:00', '2023-01-01 12:00'],
            'D50': [5.0, 10.0, 15.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'processed.parquet'
            
            processed_df, metadata = run_preprocessing_pipeline(
                input_df=df,
                output_path=output_path
            )
            
            # Check that process_duration was calculated
            assert 'process_duration' in processed_df.columns
            assert all(processed_df['process_duration'] == 2.0)
    
    def test_output_file_created(self):
        df = pd.DataFrame({
            'material_type': ['ceramic', 'metal'],
            'ball_milling_speed': [100, 200],
            'D50': [5.0, 10.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'processed.parquet'
            
            run_preprocessing_pipeline(
                input_df=df,
                output_path=output_path
            )
            
            assert output_path.exists()
            # Try to read it back
            loaded = pd.read_parquet(output_path)
            assert len(loaded) == 2
    
    def test_flagged_file_created(self):
        df = pd.DataFrame({
            'experiment_id': ['exp1', 'exp2'],
            'source': ['src1', 'src2'],
            'material_type': ['ceramic', 'metal'],
            'ball_milling_speed': [100, 200],
            'psd_image_path': ['path/to/img.png', None],
            'D50': [5.0, 10.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            flagged_path = Path(tmpdir) / 'flagged.json'
            
            run_preprocessing_pipeline(
                input_df=df,
                flagged_output_path=flagged_path
            )
            
            assert flagged_path.exists()
            with open(flagged_path, 'r') as f:
                flagged = json.load(f)
            assert len(flagged) == 1
            assert flagged[0]['experiment_id'] == 'exp1'