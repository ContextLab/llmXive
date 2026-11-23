import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
import os

from src.main import merge_datasets
from src.config import DATA_PROCESSED_PATH

@pytest.fixture
def temp_processed_dir():
    """Creates a temporary directory for processed data to avoid polluting the real data directory."""
    temp_dir = tempfile.mkdtemp()
    original_path = DATA_PROCESSED_PATH
    # We can't easily monkeypatch the constant in the module, so we rely on the function
    # creating the directory. We will ensure the function is called in a context where
    # the data is available or we mock the existence.
    # For this test, we will create the necessary input files in a temp dir and
    # manually invoke the logic, or better, test the function logic directly.
    
    # Since the function writes to DATA_PROCESSED_PATH, we will test the logic
    # and the schema validation without necessarily writing to the real path if we can avoid it,
    # but the task requires saving to data/processed/merged_dataset.csv.
    # We will use a temp dir and patch the DATA_PROCESSED_PATH or just run in a temp dir.
    # Given the constraint, we will create the temp dir and ensure the function can write there.
    # However, the function uses the constant. We will just run the test in a temp dir
    # and assume the environment is set up or we mock the path.
    # A simpler approach for the test: create temp files, call the function, verify output.
    
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_merge_schema_validation():
    """
    Verifies that merge_datasets produces data/processed/merged_dataset.csv with correct schema.
    This test MUST PASS after T014 and T018.
    """
    # Create temporary input data
    # Simulate features_df from T018-T020
    features_data = {
        'strain_accession': ['A', 'B', 'C', 'D', 'E'] * 10, # 50 samples
        'gc_content': np.random.rand(50),
        'kmer_3_count': np.random.rand(50),
        'stability_score': np.random.rand(50)
    }
    features_df = pd.DataFrame(features_data)
    
    # Simulate scores_df from T016
    scores_data = {
        'strain_accession': ['A', 'B', 'C', 'D', 'E'] * 10,
        'isg_score': np.random.rand(50)
    }
    scores_df = pd.DataFrame(scores_data)
    
    # We need to ensure the function can run. Since it writes to DATA_PROCESSED_PATH,
    # and we can't easily change the constant, we will assume the test environment
    # has the necessary permissions or we test the logic in a way that doesn't require
    # writing to the actual data directory if possible.
    # However, the task says "Save to data/processed/merged_dataset.csv".
    # We will run the function and check the file.
    
    # To avoid permission issues in the test, we can create the directory if it doesn't exist.
    processed_path = Path(DATA_PROCESSED_PATH)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    output_file = processed_path / "merged_dataset.csv"
    
    # Remove existing file if present to ensure we are testing the new run
    if output_file.exists():
        output_file.unlink()
    
    # Call the function
    result_df = merge_datasets(features_df, scores_df)
    
    # Verify the file exists
    assert output_file.exists(), "Output file merged_dataset.csv was not created."
    
    # Verify the schema
    assert 'strain_accession' in result_df.columns, "Missing 'strain_accession' column."
    assert 'isg_score' in result_df.columns, "Missing 'isg_score' column."
    assert 'gc_content' in result_df.columns, "Missing feature column 'gc_content'."
    assert 'kmer_3_count' in result_df.columns, "Missing feature column 'kmer_3_count'."
    assert 'stability_score' in result_df.columns, "Missing feature column 'stability_score'."
    
    # Verify row count (should be 50 in this case)
    assert len(result_df) == 50, f"Expected 50 rows, got {len(result_df)}."
    
    # Verify data types
    assert result_df['isg_score'].dtype in ['float64', 'float32'], "isg_score should be numeric."
    
    # Cleanup
    output_file.unlink()

def test_merge_handles_missing_strains():
    """
    Verifies that merge_datasets correctly handles missing strain links (inner join).
    """
    features_data = {
        'strain_accession': ['A', 'B', 'C', 'D'],
        'gc_content': [0.1, 0.2, 0.3, 0.4],
    }
    features_df = pd.DataFrame(features_data)
    
    scores_data = {
        'strain_accession': ['B', 'C', 'E'],
        'isg_score': [0.5, 0.6, 0.7],
    }
    scores_df = pd.DataFrame(scores_data)
    
    processed_path = Path(DATA_PROCESSED_PATH)
    processed_path.mkdir(parents=True, exist_ok=True)
    output_file = processed_path / "merged_dataset.csv"
    if output_file.exists(): output_file.unlink()
    
    result_df = merge_datasets(features_df, scores_df)
    
    # Inner join should result in only 'B' and 'C'
    assert len(result_df) == 2, f"Expected 2 rows after inner join, got {len(result_df)}."
    assert set(result_df['strain_accession'].tolist()) == {'B', 'C'}, "Incorrect strains after merge."
    
    output_file.unlink()

def test_merge_aborts_on_low_sample_count():
    """
    Verifies that merge_datasets raises RuntimeError if merged samples < 30.
    """
    features_data = {
        'strain_accession': ['A'] * 10,
        'gc_content': [0.1] * 10,
    }
    features_df = pd.DataFrame(features_data)
    
    scores_data = {
        'strain_accession': ['A'] * 10,
        'isg_score': [0.5] * 10,
    }
    scores_df = pd.DataFrame(scores_data)
    
    with pytest.raises(RuntimeError, match="FR-013 Violation"):
        merge_datasets(features_df, scores_df)
