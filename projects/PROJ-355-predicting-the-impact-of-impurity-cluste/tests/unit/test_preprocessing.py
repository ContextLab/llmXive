import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

from code.data.preprocessing import filter_zero_impurity_configs, generate_preprocessing_report, run_preprocessing_filter

@pytest.fixture
def sample_dataframe():
    data = {
        'bulk_config_id': ['id1', 'id2', 'id3', 'id4'],
        'impurity_species': ['Cr', '', None, 'Ni'],
        'segregation_energy': [0.1, 0.2, 0.3, 0.4]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_filter_zero_impurity_configs(sample_dataframe, temp_dir):
    input_file = temp_dir / 'input.csv'
    sample_dataframe.to_csv(input_file, index=False)

    filtered_df, count_excluded = filter_zero_impurity_configs(input_file)

    assert count_excluded == 2  # '' and None are excluded
    assert len(filtered_df) == 2
    assert 'Cr' in filtered_df['impurity_species'].values
    assert 'Ni' in filtered_df['impurity_species'].values
    assert '' not in filtered_df['impurity_species'].values
    assert pd.isna(filtered_df['impurity_species']).sum() == 0

def test_generate_preprocessing_report(temp_dir):
    report_path = temp_dir / 'report.json'
    generate_preprocessing_report(excluded_count=5, output_path=report_path)

    assert report_path.exists()
    with open(report_path, 'r') as f:
        report = json.load(f)

    assert report['excluded_count'] == 5
    assert report['task'] == 'T019'

def test_run_preprocessing_filter(sample_dataframe, temp_dir):
    input_file = temp_dir / 'input.csv'
    output_file = temp_dir / 'output.csv'
    report_file = temp_dir / 'report.json'

    sample_dataframe.to_csv(input_file, index=False)

    out_path, rep_path = run_preprocessing_filter(input_file, output_file, report_file)

    assert out_path.exists()
    assert rep_path.exists()
    
    # Verify output content
    out_df = pd.read_csv(out_path)
    assert len(out_df) == 2
    
    # Verify report content
    with open(rep_path, 'r') as f:
        report = json.load(f)
    assert report['excluded_count'] == 2
