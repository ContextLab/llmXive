"""
Integration tests for the load and process pipeline stages.
"""
import pytest
import os
import json
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root / "code"))

from data.loader import load_all_datasets
from data.processor import process_dataset
from config import get_config

@pytest.mark.integration
def test_load_and_process_sample_dataset(temp_dir):
    """
    Integration test: Load a small sample dataset and process it.
    Uses a synthetic CSV file to avoid external dependencies in tests.
    """
    # Create a small sample CSV
    sample_data = temp_dir / "sample.csv"
    df_sample = pd.DataFrame({
        'id': range(100),
        'value_a': range(100),
        'value_b': [x * 2 for x in range(100)],
        'category': ['A'] * 50 + ['B'] * 50
    })
    df_sample.to_csv(sample_data, index=False)

    # Load the dataset
    datasets = load_all_datasets(
        raw_dir=str(temp_dir),
        processed_dir=str(temp_dir / "processed"),
        output_dir=str(temp_dir / "output"),
        dataset_files=["sample.csv"]
    )

    assert len(datasets) == 1
    assert "sample" in datasets

    # Process the dataset
    processed = process_dataset(
        datasets["sample"],
        dataset_name="sample",
        output_dir=str(temp_dir / "output")
    )

    assert processed is not None
    assert "cleaning_report" in processed
    assert "statistical_summaries" in processed

    # Verify output files were written
    output_files = list((temp_dir / "output").glob("*.json"))
    assert len(output_files) > 0
