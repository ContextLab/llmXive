"""
Contract test for Instrument Calibration Validation (T050).
Verifies the structure and content of the instrument_calibration_report.md.
"""

import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Import the module to test
from instrument_calibration import (
    load_metadata,
    load_retrieval_results,
    bin_temperature,
    analyze_instrument_bias,
    generate_report_md
)
from utils import PipelineError

@pytest.fixture
def temp_metadata_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("planet_name,temperature,instrument\n")
        f.write("WASP-43b,1500,HST\n")
        f.write("WASP-43b,1500,HST\n") # Duplicate for stats
        f.write("HD 209458b,1400,Spitzer\n")
        f.write("HD 209458b,1400,Spitzer\n")
        f.write("Kepler-10b,2500,HST\n")
        f.write("Kepler-10b,2500,HST\n")
        f.write("Gl 12b,800,Spitzer\n")
        f.write("Gl 12b,800,Spitzer\n")
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def temp_retrieval_csv():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("planet_name,water_mixing_ratio,is_upper_limit\n")
        f.write("WASP-43b,-4.0,False\n")
        f.write("WASP-43b,-4.2,False\n")
        f.write("HD 209458b,-3.5,False\n")
        f.write("HD 209458b,-3.6,False\n")
        f.write("Kepler-10b,-5.0,False\n")
        f.write("Kepler-10b,-5.1,False\n")
        f.write("Gl 12b,-6.0,False\n")
        f.write("Gl 12b,-6.1,False\n")
        path = f.name
    yield path
    os.unlink(path)

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_bin_temperature():
    assert bin_temperature(1500.0) == 1400.0 # 1500/200 = 7.5 -> 7*200 = 1400
    assert bin_temperature(1600.0) == 1600.0
    assert bin_temperature(800.0) == 800.0
    assert np.isnan(bin_temperature(np.nan))

def test_load_metadata_valid(temp_metadata_csv):
    df = load_metadata(Path(temp_metadata_csv))
    assert 'planet_name' in df.columns
    assert 'temperature' in df.columns
    assert 'instrument' in df.columns
    assert len(df) == 8

def test_load_metadata_missing_file():
    with pytest.raises(PipelineError):
        load_metadata(Path("nonexistent.csv"))

def test_load_retrieval_results_valid(temp_retrieval_csv):
    df = load_retrieval_results(Path(temp_retrieval_csv))
    assert 'planet_name' in df.columns
    assert 'water_mixing_ratio' in df.columns
    assert 'is_upper_limit' in df.columns

def test_analyze_instrument_bias(temp_metadata_csv, temp_retrieval_csv):
    metadata_df = load_metadata(Path(temp_metadata_csv))
    retrieval_df = load_retrieval_results(Path(temp_retrieval_csv))

    result = analyze_instrument_bias(metadata_df, retrieval_df)

    assert 'instrument_bias_analysis' in result
    assert 'systematic_error_flags' in result

    analysis = result['instrument_bias_analysis']
    assert len(analysis) > 0

    # Check structure of first entry
    entry = analysis[0]
    assert 'instrument' in entry
    assert 'temperature_bin_center' in entry
    assert 'count' in entry
    assert 'mean_log10_water_mixing_ratio' in entry
    assert 'std_log10_water_mixing_ratio' in entry

def test_generate_report_md(temp_metadata_csv, temp_retrieval_csv, temp_output_dir):
    metadata_df = load_metadata(Path(temp_metadata_csv))
    retrieval_df = load_retrieval_results(Path(temp_retrieval_csv))
    analysis_data = analyze_instrument_bias(metadata_df, retrieval_df)

    output_path = temp_output_dir / "report.md"
    generate_report_md(analysis_data, output_path)

    assert output_path.exists()
    content = output_path.read_text()

    assert "Instrument-Specific Calibration Validation Report" in content
    assert "Instrument Breakdown" in content
    assert "Systematic Error Flags" in content
    assert "Conclusion" in content
    assert "HST" in content or "Spitzer" in content # Check for instrument names

def test_analyze_bias_with_upper_limits(temp_metadata_csv, temp_retrieval_csv):
    # Modify retrieval data to include upper limits
    df = pd.read_csv(temp_retrieval_csv)
    df.loc[0, 'is_upper_limit'] = True
    df.to_csv(temp_retrieval_csv, index=False)

    metadata_df = load_metadata(Path(temp_metadata_csv))
    retrieval_df = load_retrieval_results(Path(temp_retrieval_csv))

    result = analyze_instrument_bias(metadata_df, retrieval_df)
    # Should still work, just excluding the upper limit row
    assert 'instrument_bias_analysis' in result

def test_empty_merge():
    # Create dataframes with no matching planet names
    meta = pd.DataFrame({"planet_name": ["A"], "temperature": [1000], "instrument": ["HST"]})
    ret = pd.DataFrame({"planet_name": ["B"], "water_mixing_ratio": [-4.0], "is_upper_limit": [False]})

    with pytest.raises(PipelineError):
        analyze_instrument_bias(meta, ret)