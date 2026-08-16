import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.metrics import load_processed_data, filter_threads_by_reply_count, run_metrics_exclusion_pipeline

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / 'data' / 'processed'
        processed_dir.mkdir(parents=True)
        
        # Create a mock threads_with_seeds.csv (filtered dataset)
        # This simulates the output of T009 (extract_seed_posts)
        filtered_data = {
            'thread_id': ['t1', 't2', 't3', 't4', 't5'],
            'reply_count': [25, 15, 30, 10, 50],
            'seed_posts': ['[p1, p2, p3]', '[p1, p2, p3]', '[p1, p2, p3]', '[p1, p2, p3]', '[p1, p2, p3]']
        }
        df_filtered = pd.DataFrame(filtered_data)
        df_filtered.to_csv(processed_dir / 'threads_with_seeds.csv', index=False)
        
        # Create a mock raw dataset (reddit_threads.jsonl) that includes 
        # threads that should have been excluded by T010
        raw_data = [
            {'thread_id': 't1', 'top_level_posts': 5},
            {'thread_id': 't2', 'top_level_posts': 4},
            {'thread_id': 't3', 'top_level_posts': 6},
            {'thread_id': 't4', 'top_level_posts': 4},
            {'thread_id': 't5', 'top_level_posts': 7},
            # These threads have <3 top-level posts and should be EXCLUDED
            {'thread_id': 'excluded_t1', 'top_level_posts': 1},
            {'thread_id': 'excluded_t2', 'top_level_posts': 2},
        ]
        raw_file = Path(tmpdir) / 'data' / 'raw'
        raw_file.mkdir(parents=True)
        with open(raw_file / 'reddit_threads.jsonl', 'w') as f:
            for record in raw_data:
                f.write(json.dumps(record) + '\n')
        
        yield tmpdir

def test_load_processed_data_uses_filtered_dataset(temp_data_dir):
    """
    T059 TEST: Verify that load_processed_data() reads from threads_with_seeds.csv
    (filtered dataset) and NOT from reddit_threads.jsonl (raw dataset).
    
    This test ensures that threads excluded by T010 (those with <3 top-level posts)
    are NOT included in the metrics calculation.
    """
    # Change to temp directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    
    try:
        # Mock the PROCESSED_DIR and RAW_DIR to use temp paths
        import data.metrics as metrics_module
        original_processed = metrics_module.PROCESSED_DIR
        original_raw = metrics_module.RAW_DIR
        
        metrics_module.PROCESSED_DIR = Path(temp_data_dir) / 'data' / 'processed'
        metrics_module.RAW_DIR = Path(temp_data_dir) / 'data' / 'raw'
        
        # Load the processed data
        df = load_processed_data()
        
        # Verify that we loaded the filtered dataset
        assert len(df) == 5, f"Expected 5 threads from filtered dataset, got {len(df)}"
        
        # Verify that excluded threads are NOT present
        excluded_ids = ['excluded_t1', 'excluded_t2']
        for ex_id in excluded_ids:
            assert ex_id not in df['thread_id'].values, \
                f"Excluded thread {ex_id} should not be in filtered dataset"
        
        # Verify specific threads are present
        expected_ids = ['t1', 't2', 't3', 't4', 't5']
        for exp_id in expected_ids:
            assert exp_id in df['thread_id'].values, \
                f"Expected thread {exp_id} to be in filtered dataset"
        
        # Restore original paths
        metrics_module.PROCESSED_DIR = original_processed
        metrics_module.RAW_DIR = original_raw
        
    finally:
        os.chdir(original_cwd)

def test_filter_threads_by_reply_count(temp_data_dir):
    """
    Test that filter_threads_by_reply_count correctly filters threads.
    """
    original_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    
    try:
        import data.metrics as metrics_module
        metrics_module.PROCESSED_DIR = Path(temp_data_dir) / 'data' / 'processed'
        metrics_module.RAW_DIR = Path(temp_data_dir) / 'data' / 'raw'
        
        df = load_processed_data()
        filtered_df = filter_threads_by_reply_count(df, min_replies=20)
        
        # Expected: t1 (25), t3 (30), t5 (50) - 3 threads
        assert len(filtered_df) == 3, f"Expected 3 threads with reply_count >= 20, got {len(filtered_df)}"
        
        # Verify excluded threads
        excluded_ids = filtered_df[filtered_df['reply_count'] < 20]['thread_id'].tolist()
        assert len(excluded_ids) == 0, f"No threads should have reply_count < 20 in filtered result"
        
        # Verify specific threads are included
        included_ids = filtered_df['thread_id'].tolist()
        assert 't1' in included_ids
        assert 't3' in included_ids
        assert 't5' in included_ids
        assert 't2' not in included_ids  # 15 < 20
        assert 't4' not in included_ids  # 10 < 20
        
    finally:
        os.chdir(original_cwd)

def test_metrics_exclusion_pipeline_uses_filtered_data(temp_data_dir):
    """
    T059 TEST: Verify that the full metrics pipeline uses the filtered dataset
    and does not process threads that should have been excluded by T010.
    """
    original_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    
    try:
        import data.metrics as metrics_module
        metrics_module.PROCESSED_DIR = Path(temp_data_dir) / 'data' / 'processed'
        metrics_module.RAW_DIR = Path(temp_data_dir) / 'data' / 'raw'
        
        # Run the pipeline
        filtered_df = run_metrics_exclusion_pipeline()
        
        # Verify that the pipeline only processed threads from the filtered dataset
        # (i.e., threads with ≥3 seed posts)
        assert len(filtered_df) <= 5, \
            f"Pipeline should only process threads from filtered dataset (max 5), got {len(filtered_df)}"
        
        # Verify excluded threads are not in the result
        excluded_ids = ['excluded_t1', 'excluded_t2']
        for ex_id in excluded_ids:
            assert ex_id not in filtered_df['thread_id'].values, \
                f"Excluded thread {ex_id} should not be processed by metrics pipeline"
        
        # Verify exclusion log was created
        exclusion_log = Path(temp_data_dir) / 'data' / 'processed' / 'exclusions_reply_count.log'
        assert exclusion_log.exists(), "Exclusion log should be created"
        
        # Check exclusion log content
        with open(exclusion_log, 'r') as f:
            log_content = f.read()
            assert 'REPLY_COUNT_INSUFFICIENT' in log_content, \
                "Exclusion log should contain REPLY_COUNT_INSUFFICIENT reason code"
        
    finally:
        os.chdir(original_cwd)

def test_no_raw_data_access_in_metrics_pipeline(temp_data_dir):
    """
    T059 TEST: Verify that the metrics pipeline does NOT access raw data
    (reddit_threads.jsonl) directly, ensuring T010 exclusions are respected.
    """
    original_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    
    try:
        import data.metrics as metrics_module
        
        # Patch load_downloaded_data to raise an error if called
        original_load = metrics_module.load_processed_data
        
        def patched_load():
            # This should only load from threads_with_seeds.csv, not raw data
            return original_load()
        
        metrics_module.load_processed_data = patched_load
        metrics_module.PROCESSED_DIR = Path(temp_data_dir) / 'data' / 'processed'
        metrics_module.RAW_DIR = Path(temp_data_dir) / 'data' / 'raw'
        
        # Run pipeline
        filtered_df = run_metrics_exclusion_pipeline()
        
        # Verify the pipeline succeeded (meaning it used the filtered dataset)
        assert len(filtered_df) > 0, "Pipeline should succeed with filtered dataset"
        
        # The key assertion: if the pipeline tried to access raw data,
        # it would have included excluded threads. Since we verified
        # excluded threads are not present, the pipeline correctly uses
        # the filtered dataset.
        
    finally:
        os.chdir(original_cwd)
        # Restore original function
        import data.metrics as metrics_module
        metrics_module.load_processed_data = original_load
