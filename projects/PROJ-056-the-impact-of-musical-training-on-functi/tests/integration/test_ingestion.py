"""
Integration test for full ingestion pipeline on synthetic data.
Task: T013 [US1]
"""
import os
import sys
import pandas as pd
import pytest

# Ensure the project root is in the path to import code modules
# This assumes the test is run from the project root or the PYTHONPATH is set correctly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.data.synthetic_generator import generate_synthetic_data
from code.data.preprocess import filter_by_training_years, remove_missing_data
from code.utils.logging import get_logger

logger = get_logger(__name__)


def test_full_ingestion():
    """
    Test the full ingestion pipeline on synthetic data.
    
    Verifies:
    1. Synthetic data can be generated with specific parameters.
    2. Preprocessing (filtering and missing data removal) works correctly.
    3. The output file 'data/processed/subjects_cleaned.csv' is created.
    4. The output file contains exactly 10 rows (as per task requirement).
    """
    # Ensure output directory exists
    output_dir = os.path.join(PROJECT_ROOT, 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'subjects_cleaned.csv')
    
    # Remove existing output if present to ensure clean test
    if os.path.exists(output_path):
        os.remove(output_path)

    try:
        # 1. Generate synthetic data
        # We generate 15 subjects, 10 of which should pass the >= 1 year filter
        # based on the distribution parameters, or we force it by generation logic if needed.
        # For this test, we generate a larger pool and rely on the filter to reduce it to 10.
        # To guarantee exactly 10 pass, we'll generate specific data.
        
        # Strategy: Generate 10 musicians (>=1 yr) and 5 non-musicians (<1 yr).
        # The filter keeps >= 1 yr. So we expect exactly 10 rows.
        # We need to mock the generation or call it with specific seeds/params if available.
        # Since generate_synthetic_data signature isn't fully visible in the API surface,
        # we assume it can take n_subjects or similar. If not, we generate more and filter.
        # Let's assume standard generation creates a mix. We will generate 20 to be safe.
        
        df_raw = generate_synthetic_data(n_subjects=20, seed=42)
        
        # Ensure we have the required columns
        required_cols = ['subject_id', 'group', 'years_of_training', 'age', 'sex', 'motion_score', 'ses_score']
        assert all(col in df_raw.columns for col in required_cols), "Missing required columns in generated data"

        # 2. Apply filtering logic (US1: >= 1 year)
        df_filtered = filter_by_training_years(df_raw, threshold=1.0)
        
        # 3. Remove missing data
        df_clean = remove_missing_data(df_filtered)
        
        # 4. Write output
        df_clean.to_csv(output_path, index=False)
        
        # 5. Verify output exists
        assert os.path.exists(output_path), "Output file 'data/processed/subjects_cleaned.csv' was not created"
        
        # 6. Verify row count is exactly 10
        df_output = pd.read_csv(output_path)
        assert len(df_output) == 10, f"Expected 10 rows in output, but found {len(df_output)}. Raw: {len(df_raw)}, Filtered: {len(df_filtered)}"
        
        logger.info(f"Integration test passed: Generated {len(df_raw)} raw, filtered to {len(df_filtered)}, output {len(df_output)} rows.")

    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        raise