import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile

from code.data.preprocessing import run_preprocessing_filter

@pytest.fixture
def integration_data(temp_dir):
    """
    Creates a realistic CSV file simulating bulk configurations
    with a mix of valid and invalid (zero impurity) entries.
    """
    data = {
        'bulk_config_id': [f'cfg_{i}' for i in range(10)],
        'impurity_species': ['Cr', 'Ni', '', 'Fe', None, 'Cu', 'Mn', '', 'Co', 'V'],
        'crystal_system': ['BCC', 'FCC', 'BCC', 'BCC', 'FCC', 'BCC', 'FCC', 'BCC', 'FCC', 'BCC'],
        'energy': [1.0] * 10
    }
    df = pd.DataFrame(data)
    input_path = temp_dir / 'bulk_configs.csv'
    df.to_csv(input_path, index=False)
    return input_path

def test_full_preprocessing_pipeline(integration_data, temp_dir):
    """
    Integration test for T019:
    1. Loads a CSV with mixed impurity data.
    2. Filters out zero-impurity rows.
    3. Verifies the output CSV has correct count.
    4. Verifies the JSON report is generated with correct exclusion count.
    """
    output_file = temp_dir / 'bulk_configs_filtered.csv'
    report_file = temp_dir / 'preprocessing_report.json'

    out_path, rep_path = run_preprocessing_filter(
        integration_data, 
        output_file, 
        report_file
    )

    # Assertions
    assert out_path.exists(), "Output CSV should be created"
    assert rep_path.exists(), "Report JSON should be created"

    # Check output CSV
    out_df = pd.read_csv(out_path)
    # Original had 10 rows.
    # Invalid entries: '', None, '', '' (indices 2, 4, 7). Total 3.
    # Expected valid: 7.
    assert len(out_df) == 7, f"Expected 7 rows, got {len(out_df)}"
    
    # Ensure no empty strings or NaNs in impurity_species
    assert not out_df['impurity_species'].isna().any(), "No NaNs allowed in filtered data"
    assert not (out_df['impurity_species'].astype(str).str.strip() == '').any(), "No empty strings allowed"

    # Check report
    with open(rep_path, 'r') as f:
        report = json.load(f)
    
    assert report['excluded_count'] == 3, f"Expected 3 excluded, got {report['excluded_count']}"
    assert report['task'] == 'T019'