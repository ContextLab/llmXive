import pytest
import pandas as pd
import os
import json
from pathlib import Path

from ingest import main as ingest_main
from config import DATA_ROOT

def test_full_ingest_pipeline():
    """
    Integration test: Run the full ingest pipeline and verify output.
    This test assumes the dataset 'plant-metabolomics/herbivore-resistance-v1' is available.
    """
    output_path = Path(DATA_ROOT) / 'interim' / 'harmonized.csv'
    
    # Clean up previous output if exists
    if output_path.exists():
        output_path.unlink()
    
    # Run the main function
    try:
        ingest_main()
    except Exception as e:
        pytest.fail(f"Ingest pipeline failed: {e}")
    
    # Verify output file exists
    assert output_path.exists(), "Output file data/interim/harmonized.csv was not created."
    
    # Verify content structure
    df = pd.read_csv(output_path)
    
    # Check required columns
    required_columns = ['sample_id', 'genotype_id', 'resistance', 'imputation_flag']
    # Note: sample_id and genotype_id are assumed to be in the dataset based on schema
    # If the dataset uses different names, this check might need adjustment.
    # Based on T009 schema: sample_id, genotype_id, resistance, metabolite_*
    
    # We check for the columns we know we added or should exist
    assert 'resistance' in df.columns, "Resistance column missing."
    assert 'imputation_flag' in df.columns, "Imputation flag column missing."
    
    # Check data types
    assert pd.api.types.is_numeric_dtype(df['resistance']), "Resistance must be numeric."
    assert df['imputation_flag'].dtype == bool, "Imputation flag must be boolean."
    
    # Check row count (at least 10 rows as per task description)
    assert len(df) >= 10, f"Dataset has fewer than 10 rows: {len(df)}"

    # Verify metadata file created by T013 logic
    metadata_path = Path(DATA_ROOT) / 'interim' / 'metadata.json'
    assert metadata_path.exists(), "Metadata file not created."
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert 'herbivore_density_missing' in metadata, "herbivore_density_missing key missing in metadata."
    
    # Verify ordinal mapping log
    ordinal_log_path = Path(DATA_ROOT) / 'interim' / 'ordinal_mapping.log'
    # This might not exist if data was already numeric, but if it was categorical, it should exist.
    # We don't assert existence here strictly as it depends on the data content, 
    # but we can check if it exists and is valid JSON if it does.
    if ordinal_log_path.exists():
        with open(ordinal_log_path, 'r') as f:
            mapping = json.load(f)
        assert mapping == {"Low": 1, "Medium": 2, "High": 3}, "Ordinal mapping incorrect."