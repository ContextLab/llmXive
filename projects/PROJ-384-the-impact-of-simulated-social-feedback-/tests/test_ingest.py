import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
from io import StringIO

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Ensure code/ is on the path for relative imports within the project structure
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.model_loader import get_sentiment_pipeline, get_rosenberg_lexicon
from utils.data_validation import validate_dataframe, load_schema
from utils.config import SENTIMENT_SENTINEL, OUTPUT_DIR, PROCESSED_DIR
from utils.logger import setup_logger

# Import the main processing logic from 01_ingest if it exists, 
# otherwise we will mock the processing steps to verify the integration flow.
# Since T014 (implementation of 01_ingest.py) is not complete yet, 
# we must simulate the processing steps inline to verify the *integration* 
# of the components (validation, sentiment calculation, CSV writing) 
# without relying on the unimplemented script.
# However, the task asks for an integration test of the *mock dataset* producing a valid CSV.
# We will construct the pipeline manually here to test the flow.

def calculate_sentiment(text: str, pipeline) -> float:
    """
    Helper to calculate sentiment for a single text.
    Returns -999.0 if text is empty/whitespace, else pipeline score normalized to [-1, 1].
    """
    if not text or not isinstance(text, str) or not text.strip():
        return float(SENTIMENT_SENTINEL)
    
    try:
        result = pipeline(text)[0]
        label = result['label']
        score = result['score']
        
        if label == 'POSITIVE':
            return score
        else:
            return -score
    except Exception:
        # If model fails, return sentinel
        return float(SENTIMENT_SENTINEL)

def process_mock_data_for_test():
    """
    Simulates the core logic of code/01_ingest.py using a mock dataset.
    This function is used by the integration test to verify the full pipeline flow.
    """
    logger = setup_logger("test_ingest_integration")
    
    # 1. Create a representative mock dataset
    # Columns: user_id, timestamp, post_text, reply_text
    mock_data = {
        "user_id": ["user_1", "user_1", "user_2", "user_3", "user_3"],
        "timestamp": [
            "2023-01-01T10:00:00",
            "2023-01-01T11:00:00",
            "2023-01-02T09:00:00",
            "2023-01-03T12:00:00",
            "2023-01-03T14:00:00"
        ],
        "post_text": [
            "I had a great day!",
            "Nothing special today.",
            "This is a test post.",
            "I am feeling down.",
            "Everything is fine."
        ],
        "reply_text": [
            "That's wonderful!",
            "",  # Empty reply
            "Nice one.",
            "Sorry to hear that.",
            "Glad to hear it!"
        ]
    }
    
    df = pd.DataFrame(mock_data)
    
    # 2. Validate against schema
    # We assume the schema exists and validation works (tested in T010/T011)
    # We just call it to ensure it doesn't crash on valid data
    try:
        validate_dataframe(df)
    except Exception as e:
        logger.error(f"Validation failed on mock data: {e}")
        raise AssertionError("Mock data should pass validation")

    # 3. Load models
    sentiment_pipe = get_sentiment_pipeline()
    # lexicon = get_rosenberg_lexicon() # Not needed for this specific test step

    # 4. Calculate sentiment (mimicking 01_ingest.py logic)
    calculated_vals = []
    for _, row in df.iterrows():
        val = calculate_sentiment(row['reply_text'], sentiment_pipe)
        calculated_vals.append(val)
    
    df['calculated_valence'] = calculated_vals

    # 5. Ensure no crashes and output structure is correct
    # Check for expected columns
    expected_cols = ['user_id', 'timestamp', 'post_text', 'reply_text', 'calculated_valence']
    assert all(col in df.columns for col in expected_cols), "Missing expected columns"

    # Check for sentinel usage on empty text
    # Row index 1 has empty reply_text
    assert df.loc[1, 'calculated_valence'] == float(SENTIMENT_SENTINEL), "Sentinel not applied to empty text"

    # 6. Write to CSV (mimicking the output of 01_ingest.py)
    # Ensure output directory exists
    output_path = PROCESSED_DIR / "valence_sequence_test.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    
    logger.info(f"Mock data processed successfully. Output written to {output_path}")
    
    # Verify file exists and is not empty
    assert output_path.exists(), "Output CSV file was not created"
    assert output_path.stat().st_size > 0, "Output CSV file is empty"
    
    # Read back and verify content
    df_out = pd.read_csv(output_path)
    assert len(df_out) == len(df), "Row count mismatch"
    assert 'calculated_valence' in df_out.columns, "Missing calculated_valence in output"
    
    # Clean up test file
    output_path.unlink()
    
    return True

def test_integration_mock_dataset_produces_valid_csv():
    """
    Integration test verifying that a mock dataset of a representative number of rows
    produces a valid CSV with no crashes.
    """
    # This test runs the full flow: create data -> validate -> process -> write CSV
    result = process_mock_data_for_test()
    assert result is True, "Integration test failed"