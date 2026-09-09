import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from ingestion.consolidate_data import (
    load_scrubbed_timeseries,
    load_behavioral_scores,
    load_motion_params,
    merge_datasets,
    validate_consolidated_data,
    main
)

class TestConsolidateData:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up test fixtures and clean up after tests."""
        # Create temporary directory structure
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data" / "processed"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock file paths
        self.scrubbed_path = self.data_dir / "scrubbed_timeseries.parquet"
        self.behavioral_path = self.data_dir / "behavioral_scores.parquet"
        self.motion_path = self.data_dir / "motion_params.parquet"
        self.output_path = self.data_dir / "consolidated_data.parquet"
        
        # Create mock data
        self.mock_timeseries = pd.DataFrame({
            'subject_id': ['sub-001', 'sub-001', 'sub-002', 'sub-002'],
            'time_point': [1, 2, 1, 2],
            'region_1': [0.5, 0.6, 0.7, 0.8],
            'region_2': [0.3, 0.4, 0.5, 0.6]
        })
        
        self.mock_behavioral = pd.DataFrame({
            'subject_id': ['sub-001', 'sub-002', 'sub-003'],
            'accuracy': [0.85, 0.72, 0.91]
        })
        
        self.mock_motion = pd.DataFrame({
            'subject_id': ['sub-001', 'sub-002'],
            'mean_fd': [0.15, 0.25]
        })
        
        # Write mock data to files
        self.mock_timeseries.to_parquet(self.scrubbed_path)
        self.mock_behavioral.to_parquet(self.behavioral_path)
        self.mock_motion.to_parquet(self.motion_path)
        
        # Temporarily override global paths
        self.original_scrubbed_path = None
        self.original_behavioral_path = None
        self.original_motion_path = None
        self.original_output_path = None
        
        # We need to monkeypatch the module's global variables
        import ingestion.consolidate_data as cd_module
        self.original_scrubbed_path = cd_module.SCRUBBED_TIMESERIES_PATH
        self.original_behavioral_path = cd_module.BEHAVIORAL_SCORES_PATH
        self.original_motion_path = cd_module.PROJECT_ROOT / "data" / "processed" / "motion_params.parquet"
        self.original_output_path = cd_module.OUTPUT_PATH
        
        cd_module.SCRUBBED_TIMESERIES_PATH = self.scrubbed_path
        cd_module.BEHAVIORAL_SCORES_PATH = self.behavioral_path
        cd_module.PROJECT_ROOT = Path(self.temp_dir)
        cd_module.OUTPUT_PATH = self.output_path
        
        yield
        
        # Restore original paths
        cd_module.SCRUBBED_TIMESERIES_PATH = self.original_scrubbed_path
        cd_module.BEHAVIORAL_SCORES_PATH = self.original_behavioral_path
        cd_module.PROJECT_ROOT = Path(project_root)
        cd_module.OUTPUT_PATH = self.original_output_path
        
        # Clean up
        shutil.rmtree(self.temp_dir)

    def test_load_scrubbed_timeseries(self):
        """Test loading scrubbed timeseries data."""
        df = load_scrubbed_timeseries()
        assert not df.empty
        assert 'subject_id' in df.columns
        assert 'time_point' in df.columns

    def test_load_behavioral_scores(self):
        """Test loading behavioral scores data."""
        df = load_behavioral_scores()
        assert not df.empty
        assert 'subject_id' in df.columns
        assert 'accuracy' in df.columns

    def test_load_motion_params(self):
        """Test loading motion parameters."""
        df = load_motion_params()
        assert not df.empty
        assert 'subject_id' in df.columns
        assert 'mean_fd' in df.columns

    def test_merge_datasets(self):
        """Test merging datasets."""
        timeseries_df = load_scrubbed_timeseries()
        behavioral_df = load_behavioral_scores()
        motion_df = load_motion_params()
        
        merged = merge_datasets(timeseries_df, behavioral_df, motion_df)
        
        # Should have 2 subjects (sub-001 and sub-002) - inner join
        assert len(merged) == 2
        assert 'subject_id' in merged.columns
        assert 'accuracy' in merged.columns
        assert 'mean_fd' in merged.columns
        
        # Check specific values
        sub001 = merged[merged['subject_id'] == 'sub-001'].iloc[0]
        assert sub001['accuracy'] == 0.85
        assert sub001['mean_fd'] == 0.15

    def test_merge_datasets_without_motion(self):
        """Test merging datasets when motion data is missing for some subjects."""
        timeseries_df = load_scrubbed_timeseries()
        behavioral_df = load_behavioral_scores()
        motion_df = pd.DataFrame({
            'subject_id': ['sub-001'],
            'mean_fd': [0.15]
        })
        
        merged = merge_datasets(timeseries_df, behavioral_df, motion_df)
        
        # Should have 2 subjects
        assert len(merged) == 2
        
        # sub-002 should have NaN for mean_fd
        sub002 = merged[merged['subject_id'] == 'sub-002'].iloc[0]
        assert pd.isna(sub002['mean_fd'])

    def test_validate_consolidated_data(self):
        """Test validation of consolidated data."""
        timeseries_df = load_scrubbed_timeseries()
        behavioral_df = load_behavioral_scores()
        motion_df = load_motion_params()
        
        merged = merge_datasets(timeseries_df, behavioral_df, motion_df)
        
        # Should pass validation
        assert validate_consolidated_data(merged) is True

    def test_validate_consolidated_data_empty(self):
        """Test validation fails on empty data."""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="Consolidated dataset is empty"):
            validate_consolidated_data(empty_df)

    def test_validate_consolidated_data_missing_column(self):
        """Test validation fails on missing critical column."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="missing 'subject_id'"):
            validate_consolidated_data(df)

    def test_main_function(self):
        """Test the main function creates output file."""
        # Run main
        main()
        
        # Check output file exists
        assert self.output_path.exists()
        
        # Check output content
        output_df = pd.read_parquet(self.output_path)
        assert not output_df.empty
        assert 'subject_id' in output_df.columns
        assert 'accuracy' in output_df.columns

    def test_main_missing_files(self, monkeypatch):
        """Test main function fails gracefully when files are missing."""
        import ingestion.consolidate_data as cd_module
        
        # Temporarily set paths to non-existent files
        original_path = cd_module.SCRUBBED_TIMESERIES_PATH
        cd_module.SCRUBBED_TIMESERIES_PATH = Path("/nonexistent/path.parquet")
        
        with pytest.raises(SystemExit):
            main()
        
        # Restore
        cd_module.SCRUBBED_TIMESERIES_PATH = original_path

    def test_merge_with_no_common_subjects(self):
        """Test merging when there are no common subjects."""
        timeseries_df = pd.DataFrame({
            'subject_id': ['sub-001', 'sub-002'],
            'time_point': [1, 2],
            'region_1': [0.5, 0.6]
        })
        
        behavioral_df = pd.DataFrame({
            'subject_id': ['sub-003', 'sub-004'],
            'accuracy': [0.85, 0.72]
        })
        
        merged = merge_datasets(timeseries_df, behavioral_df)
        
        # Inner join should result in empty DataFrame
        assert len(merged) == 0