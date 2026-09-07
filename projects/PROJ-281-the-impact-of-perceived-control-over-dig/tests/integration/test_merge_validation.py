"""
Integration test for the merge and save pipeline (T032).

This test verifies that:
1. Scoring and proxy results can be loaded
2. Datasets merge correctly on post_id
3. Final output contains expected columns
4. No data leakage occurs (text column not in proxy results)
"""
import pytest
import pandas as pd
from pathlib import Path
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the functions we're testing
from code.services.merge_and_save import (
    load_scoring_results,
    load_proxy_results,
    merge_datasets,
    save_final_analysis,
    run_merge_and_save_pipeline
)
from code.config import CONFIG


class TestMergeValidation:
    """Test suite for merge and save functionality."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        processed_dir = Path(temp_dir) / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Patch CONFIG to use temp directory
        original_processed_dir = CONFIG.PROCESSED_DATA_DIR
        
        class MockConfig:
            PROCESSED_DATA_DIR = processed_dir
        
        with patch.object(CONFIG, 'PROCESSED_DATA_DIR', processed_dir):
            yield processed_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_load_scoring_results_missing_file(self, temp_data_dir):
        """Test that missing scoring results file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Scoring results file not found"):
            load_scoring_results()
    
    def test_load_proxy_results_missing_file(self, temp_data_dir):
        """Test that missing proxy results file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Proxy results file not found"):
            load_proxy_results()
    
    def test_merge_datasets_invalid_key(self, temp_data_dir):
        """Test that merge fails with invalid join key."""
        scoring_df = pd.DataFrame({'post_id': [1, 2], 'anxiety_score': [0.5, 0.8]})
        proxy_df = pd.DataFrame({'post_id': [1, 2], 'control_proxy': [0.3, 0.6]})
        
        with pytest.raises(ValueError, match="Join key 'invalid_key' not found"):
            merge_datasets(scoring_df, proxy_df, join_key='invalid_key')
    
    def test_merge_datasets_inner_join(self, temp_data_dir):
        """Test that merge performs inner join correctly."""
        scoring_df = pd.DataFrame({
            'post_id': [1, 2, 3],
            'anxiety_score': [0.5, 0.8, 0.3]
        })
        proxy_df = pd.DataFrame({
            'post_id': [2, 3, 4],
            'control_proxy': [0.6, 0.4, 0.7]
        })
        
        merged = merge_datasets(scoring_df, proxy_df)
        
        # Should only have posts 2 and 3 (inner join)
        assert len(merged) == 2
        assert set(merged['post_id'].tolist()) == {2, 3}
        assert 'anxiety_score' in merged.columns
        assert 'control_proxy' in merged.columns
    
    def test_save_final_analysis_creates_file(self, temp_data_dir):
        """Test that save_final_analysis creates the output file."""
        merged_df = pd.DataFrame({
            'post_id': [1, 2],
            'anxiety_score': [0.5, 0.8],
            'control_proxy': [0.3, 0.6]
        })
        
        output_path = save_final_analysis(merged_df)
        
        assert output_path.exists()
        assert output_path.name == 'final_analysis.csv'
        
        # Verify content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == 2
        assert set(saved_df.columns) == {'post_id', 'anxiety_score', 'control_proxy'}
    
    def test_save_final_analysis_empty_dataframe(self, temp_data_dir):
        """Test that saving empty DataFrame raises ValueError."""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="Cannot save empty DataFrame"):
            save_final_analysis(empty_df)
    
    def test_merge_preserves_data_integrity(self, temp_data_dir):
        """Test that merge preserves all relevant data columns."""
        scoring_df = pd.DataFrame({
            'post_id': [1, 2, 3],
            'anxiety_score': [0.5, 0.8, 0.3],
            'confidence_score': [0.9, 0.95, 0.85]
        })
        proxy_df = pd.DataFrame({
            'post_id': [1, 2, 3],
            'user_id': ['user1', 'user2', 'user3'],
            'control_proxy': [0.3, 0.6, 0.4],
            'timestamp_regularity': [0.8, 0.9, 0.7]
        })
        
        merged = merge_datasets(scoring_df, proxy_df)
        
        # Verify all columns present
        expected_columns = {
            'post_id', 'anxiety_score', 'confidence_score',
            'user_id', 'control_proxy', 'timestamp_regularity'
        }
        assert set(merged.columns) == expected_columns
        
        # Verify data values
        assert merged.loc[merged['post_id'] == 1, 'anxiety_score'].iloc[0] == 0.5
        assert merged.loc[merged['post_id'] == 1, 'control_proxy'].iloc[0] == 0.3
        assert merged.loc[merged['post_id'] == 1, 'user_id'].iloc[0] == 'user1'
    
    def test_no_text_column_in_proxy_results(self, temp_data_dir):
        """
        Test that proxy results do not contain text column.
        This verifies Constitution Principle VI compliance.
        """
        proxy_df = pd.DataFrame({
            'post_id': [1, 2],
            'user_id': ['user1', 'user2'],
            'control_proxy': [0.3, 0.6],
            'timestamp_regularity': [0.8, 0.9]
        })
        
        # Save proxy results
        proxy_path = temp_data_dir / "proxy_results.csv"
        proxy_df.to_csv(proxy_path, index=False)
        
        # Load and verify no text column
        loaded_proxy = load_proxy_results()
        assert 'text' not in loaded_proxy.columns
    
    def test_full_pipeline_integration(self, temp_data_dir):
        """
        Test the full merge and save pipeline with realistic data.
        """
        # Create realistic scoring results
        scoring_df = pd.DataFrame({
            'post_id': [f'post_{i}' for i in range(100)],
            'anxiety_score': [0.1 * i for i in range(100)],
            'confidence_score': [0.8 + 0.001 * i for i in range(100)]
        })
        
        # Create realistic proxy results (some overlap, some not)
        proxy_df = pd.DataFrame({
            'post_id': [f'post_{i}' for i in range(50, 150)],
            'user_id': [f'user_{i % 10}' for i in range(100)],
            'control_proxy': [0.1 * (i % 10) for i in range(100)],
            'timestamp_regularity': [0.7 + 0.002 * (i % 10) for i in range(100)]
        })
        
        # Save both files
        scoring_path = temp_data_dir / "scoring_results.csv"
        proxy_path = temp_data_dir / "proxy_results.csv"
        scoring_df.to_csv(scoring_path, index=False)
        proxy_df.to_csv(proxy_path, index=False)
        
        # Run the pipeline
        output_path = run_merge_and_save_pipeline()
        
        # Verify output
        assert output_path.exists()
        final_df = pd.read_csv(output_path)
        
        # Should have 50 matched rows (posts 50-99)
        assert len(final_df) == 50
        
        # Verify columns
        expected_columns = {
            'post_id', 'anxiety_score', 'confidence_score',
            'user_id', 'control_proxy', 'timestamp_regularity'
        }
        assert set(final_df.columns) == expected_columns
        
        # Verify data integrity
        assert final_df['post_id'].is_monotonic_increasing
        assert all(final_df['anxiety_score'] >= 0)
        assert all(final_df['control_proxy'] >= 0)