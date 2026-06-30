from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from analysis.regression import compute_correlations_and_effect_sizes, write_correlation_effects_report, CorrelationResult, EffectSizeResult

def _sample_dataframe() -> pd.DataFrame:
    # Minimal synthetic dataset covering required columns.
    # Based on the actual API surface: analysis.regression uses these columns.
    data = {
        "crossing_number": [3.0, 4.0, 5.0, 6.0, 7.0],
        "braid_index": [2.0, 2.0, 3.0, 3.0, 4.0],
        "hyperbolic_volume": [0.9, 2.0, 2.8, 3.5, 4.2],
        "alternating": [True, True, False, False, False],
    }
    return pd.DataFrame(data)

def test_compute_correlations_and_effect_sizes():
    df = _sample_dataframe()
    # The function expects specific columns as per the implementation in analysis.regression
    # It computes Pearson/Spearman for (crossing, braid), (crossing, volume), (braid, volume)
    # and returns a list of CorrelationResult and EffectSizeResult
    try:
        results = compute_correlations_and_effect_sizes(df)
        # We expect results to be non-empty if the function runs correctly
        assert len(results) > 0, "Expected correlation results"
        
        # Verify structure of CorrelationResult
        for res in results:
            assert isinstance(res, CorrelationResult)
            assert res.metric_name is not None
            assert isinstance(res.value, (float, int))
            # p-value is N/A per project constraints (census data)
            assert res.p_value == "N/A"
    except Exception as e:
        # If the function signature or logic has changed, we fail explicitly
        raise AssertionError(f"compute_correlations_and_effect_sizes failed: {e}")

def test_write_correlation_effects_report(tmp_path: Path):
    df = _sample_dataframe()
    out_dir = tmp_path / "data" / "processed"
    out_dir.mkdir(parents=True)
    
    report_path = out_dir / "correlation_effects_report.json"
    
    try:
        write_correlation_effects_report(df, report_path)
        assert report_path.exists(), "Report file was not created"
        
        with report_path.open() as f:
            data = json.load(f)
        
        assert isinstance(data, list), "Report should be a list of results"
        assert len(data) > 0, "Report should contain entries"
        
        # Check that p-values are marked as N/A in the output
        for entry in data:
            if "p_value" in entry:
                assert entry["p_value"] == "N/A", "p-value must be N/A for census data"
    except Exception as e:
        raise AssertionError(f"write_correlation_effects_report failed: {e}")

def test_main_writes_outputs(tmp_path: Path, monkeypatch):
    # Redirect data output directory to a temporary location
    out_dir = tmp_path / "data" / "processed"
    out_dir.mkdir(parents=True)
    
    # Create a minimal cleaned knots CSV that the main function will read
    df = _sample_dataframe()
    csv_path = out_dir / "knots_cleaned.csv"
    df.to_csv(csv_path, index=False)
    
    # Monkeypatch the path used by analysis._utils
    import analysis._utils
    original_path = analysis._utils._PROCESSED_PATH
    analysis._utils._PROCESSED_PATH = csv_path
    
    try:
        from analysis.regression import main
        main()
        
        # Verify output files exist
        report_file = out_dir / "correlation_effects_report.json"
        assert report_file.is_file(), "correlation_effects_report.json not found"
        
        with report_file.open() as f:
            content = json.load(f)
        assert isinstance(content, list)
    finally:
        # Restore original path
        analysis._utils._PROCESSED_PATH = original_path