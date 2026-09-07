import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

# Simulating the import structure
# In a real run, this would be: from code.data.preprocessing import run_preprocessing_filter
# but for unit testing the flow, we import the components
from code.data.preprocessing import filter_zero_impurity_configs, generate_preprocessing_report

def test_full_preprocessing_flow(tmp_path):
    """
    Integration test: Create a CSV with mixed impurity counts, run filter, verify report.
    """
    # Setup
    input_file = tmp_path / "descriptors.csv"
    report_file = tmp_path / "preprocessing_report.json"
    
    # Create test data
    data = {
        'config_id': [1, 2, 3, 4, 5],
        'impurity_count': [0, 1, 0, 2, 1],
        'rdf_peak': [1.0, 2.0, 3.0, 4.0, 5.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(input_file, index=False)
    
    # Execute logic (mimicking run_preprocessing_filter)
    loaded_df = pd.read_csv(input_file)
    filtered_df, excluded_count = filter_zero_impurity_configs(loaded_df)
    
    # Save filtered (simulating pipeline step)
    filtered_df.to_csv(tmp_path / "descriptors_filtered.csv", index=False)
    
    # Generate report
    generate_preprocessing_report(excluded_count, report_file)
    
    # Verify
    assert report_file.exists()
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    assert report['excluded_count'] == 2
    assert report['status'] == 'completed'
    
    # Verify filtered data
    assert len(filtered_df) == 3
    assert all(filtered_df['impurity_count'] > 0)