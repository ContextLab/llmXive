"""
Unit tests for noise_stability.py (Task T047).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os

# Mock config for testing
MOCK_CONFIG = {
    "paths": {
        "processed": "data/processed",
        "results": "results",
        "logs": "logs"
    }
}

from noise_stability import load_metadata, calculate_snr_cv, analyze_instrument_stability

class TestLoadMetadata:
    def test_load_metadata_success(self, tmp_path):
        """Test loading a valid metadata file."""
        # Create temp directory structure
        proc_dir = tmp_path / "data" / "processed"
        proc_dir.mkdir(parents=True)
        
        csv_path = proc_dir / "metadata.csv"
        data = {
            "planet_name": ["p1", "p2"],
            "snr": [10.0, 20.0],
            "instrument": ["HST", "JWST"]
        }
        df_test = pd.DataFrame(data)
        df_test.to_csv(csv_path, index=False)
        
        # Mock config
        test_config = {"paths": {"processed": str(proc_dir)}}
        
        result_df = load_metadata(test_config)
        
        assert len(result_df) == 2
        assert "snr" in result_df.columns
        assert "instrument" in result_df.columns
        assert result_df["snr"].mean() == 15.0

    def test_load_metadata_missing_file(self, tmp_path):
        """Test loading when file does not exist."""
        proc_dir = tmp_path / "data" / "processed"
        proc_dir.mkdir(parents=True)
        
        test_config = {"paths": {"processed": str(proc_dir)}}
        
        with pytest.raises(FileNotFoundError):
            load_metadata(test_config)

    def test_load_metadata_missing_columns(self, tmp_path):
        """Test loading when required columns are missing."""
        proc_dir = tmp_path / "data" / "processed"
        proc_dir.mkdir(parents=True)
        
        csv_path = proc_dir / "metadata.csv"
        data = {
            "planet_name": ["p1"],
            "other_col": [10.0]
        }
        pd.DataFrame(data).to_csv(csv_path, index=False)
        
        test_config = {"paths": {"processed": str(proc_dir)}}
        
        with pytest.raises(ValueError, match="missing required columns"):
            load_metadata(test_config)

class TestCalculateSnrCv:
    def test_cv_calculation(self):
        """Test CV calculation."""
        df = pd.DataFrame({"snr": [10.0, 20.0, 30.0]})
        # Mean = 20, Std = 8.165... -> CV = 0.408...
        cv = calculate_snr_cv(df)
        expected_mean = 20.0
        expected_std = df["snr"].std()
        expected_cv = expected_std / expected_mean
        
        assert np.isclose(cv, expected_cv)

    def test_cv_zero_mean(self):
        """Test CV calculation with zero mean."""
        df = pd.DataFrame({"snr": [0.0, 0.0]})
        cv = calculate_snr_cv(df)
        assert cv == 0.0

class TestAnalyzeInstrumentStability:
    def test_stability_analysis(self):
        """Test full stability analysis logic."""
        # Create data with two instruments: one stable, one unstable
        data = {
            "snr": [100.0, 100.0, 100.0,  # Stable instrument (CV ~ 0)
                    10.0, 50.0, 90.0],    # Unstable instrument (High CV)
            "instrument": ["Stable", "Stable", "Stable",
                           "Unstable", "Unstable", "Unstable"]
        }
        df = pd.DataFrame(data)
        
        results = analyze_instrument_stability(df, threshold=0.20)
        
        assert "instrument_stats" in results
        assert "flagged_instruments" in results
        assert "global_cv" in results
        
        # Check stable instrument
        assert results["instrument_stats"]["Stable"]["cv"] < 0.20
        # Check unstable instrument
        assert results["instrument_stats"]["Unstable"]["cv"] > 0.20
        assert "Unstable" in results["flagged_instruments"]
        assert "Stable" not in results["flagged_instruments"]

    def test_flagging_threshold(self):
        """Test that threshold parameter works."""
        data = {
            "snr": [10.0, 12.0], # CV ~ 0.18 (below 0.20)
            "instrument": ["Inst", "Inst"]
        }
        df = pd.DataFrame(data)
        
        results = analyze_instrument_stability(df, threshold=0.10)
        
        # With threshold 0.10, this should be flagged
        assert "Inst" in results["flagged_instruments"]

        results_loose = analyze_instrument_stability(df, threshold=0.30)
        # With threshold 0.30, this should NOT be flagged
        assert "Inst" not in results_loose["flagged_instruments"]
