import os
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
import requests
from unittest.mock import patch, MagicMock
import json

# Import project modules
from code.config import ACE_URL, NOAA_URL, TRAIN_START, TRAIN_END
from code.data.fetch import fetch_ace, fetch_noaa
from code.data.align import run_alignment
from code.analysis.thresholds import write_global_thresholds
from code.viz.report_generation import run_report_generation

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent

def load_schema(schema_path):
    """Load a JSON schema from a file."""
    with open(schema_path, 'r') as f:
        return json.load(f)

def validate_against_schema(data, schema):
    """Validate data against a JSON schema."""
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        return True
    except Exception as e:
        raise AssertionError(f"Schema validation failed: {e}")

def test_pipeline_monthly_sync():
    """
    Integration test for full month download and sync.
    Asserts that data comes from verified URLs and fails on network issues.
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    fixtures_dir = project_root / "data" / "fixtures"
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    
    # Define test window (1 month)
    start_date = f"{TRAIN_START}-01-01"
    end_date = f"{TRAIN_START}-02-01"
    
    # 1. Verify that fetch_ace uses the verified URL
    # We mock the actual network call but assert the URL used
    mock_ace_content = "Date,Time,N_p,T_p,He2+_ratio\n1998-01-01,00:00,5.0,10.0,0.05\n"
    
    with patch('code.data.fetch.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = mock_ace_content
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Call fetch
        ace_path = fetch_ace(start_date, end_date)
        
        # Assert the correct URL was used
        mock_get.assert_called()
        called_url = mock_get.call_args[0][0]
        assert ACE_URL in called_url or "spdf.gsfc.nasa.gov" in called_url, \
            f"Fetch used incorrect URL: {called_url}. Expected to use verified ACE_URL."
    
    # 2. Verify that fetch_noaa uses the verified URL
    mock_noaa_content = "Date,Time,Kp,Dst\n1998-01-01,00:00,2,50\n"
    
    with patch('code.data.fetch.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = mock_noaa_content
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Call fetch
        noaa_path = fetch_noaa(start_date, end_date)
        
        # Assert the correct URL was used
        mock_get.assert_called()
        called_url = mock_get.call_args[0][0]
        assert NOAA_URL in called_url or "swpc.noaa.gov" in called_url, \
            f"Fetch used incorrect URL: {called_url}. Expected to use verified NOAA_URL."

    # 3. Test that the pipeline FAILS LOUDLY if the real URL is unreachable
    # (Simulating network failure)
    with patch('code.data.fetch.requests.get') as mock_get:
        mock_get.side_effect = requests.ConnectionError("Network unreachable")
        
        with pytest.raises((requests.ConnectionError, OSError)) as exc_info:
            # This should NOT fall back to synthetic data
            fetch_ace(start_date, end_date)
        
        # Verify the failure was a network error, not a synthetic fallback
        assert "Network unreachable" in str(exc_info.value) or "ConnectionError" in str(type(exc_info.value))

    # 4. Run the alignment pipeline with the mocked data files created above
    # (In a real run, these files would be populated by the fetch calls above)
    # For this test, we assume the files exist in data/raw/ or we create minimal valid ones
    # to verify the sync logic works end-to-end.
    
    # Create minimal valid raw files if they don't exist (simulating successful fetch)
    # Note: In a real CI/CD, these would be downloaded. Here we ensure the path exists for the test.
    ace_file = raw_dir / "ace_raw.csv"
    noaa_file = raw_dir / "noaa_raw.csv"
    
    if not ace_file.exists():
        with open(ace_file, 'w') as f:
            f.write("Date,Time,N_p,T_p,He2+_ratio\n1998-01-01,00:00,5.0,10.0,0.05\n")
    if not noaa_file.exists():
        with open(noaa_file, 'w') as f:
            f.write("Date,Time,Kp,Dst\n1998-01-01,00:00,2,50\n")
    
    # Run alignment
    output_path = processed_dir / "synced.csv"
    run_alignment(start_date, end_date, str(output_path))
    
    # Verify output exists
    assert output_path.exists(), f"Output file {output_path} was not created."
    
    # Verify schema conformance
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    # Note: jsonschema expects JSON, but we have YAML. We'll do a basic structural check
    # or load the YAML if pyyaml is available.
    df = pd.read_csv(output_path)
    
    required_cols = ['timestamp', 'proton_density', 'temperature', 'helium_abundance', 'Kp', 'Dst']
    assert list(df.columns) == required_cols, \
        f"Columns mismatch. Expected {required_cols}, got {list(df.columns)}"
    
    assert df.isnull().sum().sum() == 0, "Output contains NaN values after interpolation."

def test_pipeline_correlation_full_run():
    """
    Integration test for full correlation run.
    Verifies artifacts/correlations.csv structure and row count.
    """
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    artifacts_dir = project_root / "artifacts"
    
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure synced.csv exists (from previous test or fixture)
    synced_path = processed_dir / "synced.csv"
    if not synced_path.exists():
        # Create a minimal valid dataset for the test
        df = pd.DataFrame({
            'timestamp': pd.date_range(start='1998-01-01', periods=100, freq='H'),
            'proton_density': np.random.rand(100) * 10,
            'temperature': np.random.rand(100) * 20,
            'helium_abundance': np.random.rand(100) * 1,
            'Kp': np.random.randint(0, 9, 100),
            'Dst': np.random.randint(-100, 100, 100)
        })
        synced_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(synced_path, index=False)
    
    # Run correlation analysis
    from code.analysis.correlation import run_correlation_analysis
    output_path = artifacts_dir / "correlations.csv"
    
    # This should run without error
    run_correlation_analysis(str(synced_path), str(output_path))
    
    # Verify output
    assert output_path.exists(), f"Correlation results file {output_path} not created."
    
    df_corr = pd.read_csv(output_path)
    
    # Verify schema conformance
    required_cols = ['composition_parameter', 'geomagnetic_index', 'lag_hours', 
                     'pearson_r', 'spearman_rho', 'p_raw', 'p_bonferroni', 'significance_flag']
    assert list(df_corr.columns) == required_cols, \
        f"Correlation columns mismatch. Expected {required_cols}, got {list(df_corr.columns)}"
    
    # Verify row count (3 params * 2 indices * 5 lags = 30)
    expected_rows = 30
    assert len(df_corr) == expected_rows, \
        f"Expected {expected_rows} rows, got {len(df_corr)}"

def test_pipeline_validation_full_run():
    """
    Integration test for full validation run.
    Verifies artifacts exist and report is generated.
    """
    project_root = get_project_root()
    artifacts_dir = project_root / "artifacts"
    reports_dir = artifacts_dir / "reports"
    thresholds_dir = artifacts_dir / "thresholds"
    
    reports_dir.mkdir(parents=True, exist_ok=True)
    thresholds_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure prerequisites exist
    # 1. Correlation results
    corr_path = artifacts_dir / "correlations.csv"
    if not corr_path.exists():
        # Create dummy data
        df = pd.DataFrame({
            'composition_parameter': ['proton_density'] * 10,
            'geomagnetic_index': ['Kp'] * 10,
            'lag_hours': list(range(10)),
            'pearson_r': np.random.rand(10),
            'spearman_rho': np.random.rand(10),
            'p_raw': np.random.rand(10),
            'p_bonferroni': np.random.rand(10),
            'significance_flag': [False] * 10
        })
        df.to_csv(corr_path, index=False)
    
    # 2. Global thresholds
    threshold_path = thresholds_dir / "global_threshold.json"
    if not threshold_path.exists():
        threshold_data = {
            "neff_values": {"proton_density": 0.8, "temperature": 0.8, "helium_abundance": 0.8},
            "alpha_adj": 0.0016666666666666668,
            "total_tests": 30
        }
        with open(threshold_path, 'w') as f:
            json.dump(threshold_data, f)
    
    # Run validation report generation
    report_path = reports_dir / "validation_report.md"
    run_report_generation(
        corr_path=str(corr_path),
        threshold_path=str(threshold_path),
        output_path=str(report_path)
    )
    
    # Verify report exists
    assert report_path.exists(), f"Validation report {report_path} not created."
    
    # Verify content contains expected markers
    with open(report_path, 'r') as f:
        content = f.read()
    
    assert "Helium" in content or "proton" in content, "Report should mention composition parameters."
    assert "Dst" in content or "Kp" in content, "Report should mention geomagnetic indices."