"""
Tests for the analysis module, specifically T025 Residual Diagnostics.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis import (
    perform_residual_diagnostics,
    perform_residual_diagnostics_full,
    save_analysis_results,
    load_gate_status,
    load_stat_gate_status,
    main,
)


class TestResidualDiagnostics:
    """Tests for T025: Residual Diagnostics."""

    def test_shapiro_wilk_normality(self):
        """Test that Shapiro-Wilk test returns valid statistics."""
        # Create a mock model with normal residuals
        residuals = np.random.normal(0, 1, 100)
        mock_model = MagicMock()
        mock_model.resid = residuals
        mock_model.model.exog = np.ones((100, 1))  # Dummy exog

        result = perform_residual_diagnostics(mock_model)

        assert "shapiro_wilk" in result
        assert "stat" in result["shapiro_wilk"]
        assert "p" in result["shapiro_wilk"]
        assert 0 <= result["shapiro_wilk"]["stat"] <= 1
        assert 0 <= result["shapiro_wilk"]["p"] <= 1

    def test_breusch_pagan_homoscedasticity(self):
        """Test that Breusch-Pagan test returns valid statistics."""
        # Create a mock model with homoscedastic residuals
        n = 100
        residuals = np.random.normal(0, 1, n)
        exog = np.random.normal(0, 1, (n, 2))

        mock_model = MagicMock()
        mock_model.resid = residuals
        mock_model.model.exog = exog

        result = perform_residual_diagnostics(mock_model)

        assert "breusch_pagan" in result
        assert "stat" in result["breusch_pagan"]
        assert "p" in result["breusch_pagan"]
        # Stat should be non-negative
        assert result["breusch_pagan"]["stat"] >= 0
        assert 0 <= result["breusch_pagan"]["p"] <= 1

    def test_full_diagnostics_integration(self, tmp_path):
        """Integration test for full diagnostics pipeline."""
        # Create a temporary standard_subset.csv
        data = {
            "mw": [100, 200, 300, 400, 500],
            "tpsa": [10, 20, 30, 40, 50],
            "rotatable_bonds": [1, 2, 3, 4, 5],
            "aromatic_rings": [1, 1, 2, 2, 3],
            "wiener_index": [5.0, 10.0, 15.0, 20.0, 25.0],
            "zagreb_index": [1.0, 2.0, 3.0, 4.0, 5.0],
            "half_life": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "standard_subset.csv"
        df.to_csv(csv_path, index=False)

        # Mock gate status files
        gate_status_path = tmp_path / "gate_status.json"
        stat_gate_status_path = tmp_path / "stat_gate_status.json"
        with open(gate_status_path, "w") as f:
            json.dump({"status": "PASS"}, f)
        with open(stat_gate_status_path, "w") as f:
            json.dump({"status": "PASS"}, f)

        # Patch paths
        with patch("analysis.PROCESSED_DIR", tmp_path):
            with patch("analysis.load_gate_status", return_value={"status": "PASS"}):
                with patch("analysis.load_stat_gate_status", return_value={"status": "PASS"}):
                    with patch("analysis.save_analysis_results") as mock_save:
                        # Run the function
                        result = perform_residual_diagnostics_full(df)

                        # Verify result structure
                        assert result["status"] == "PASS"
                        assert "shapiro_wilk" in result
                        assert "breusch_pagan" in result
                        assert "stat" in result["shapiro_wilk"]
                        assert "p" in result["shapiro_wilk"]
                        assert "stat" in result["breusch_pagan"]
                        assert "p" in result["breusch_pagan"]

    def test_save_analysis_results(self, tmp_path):
        """Test that analysis results are saved correctly."""
        results = {
            "status": "PASS",
            "N": 10,
            "R2": 0.85,
            "p_values": {"x": 0.01},
            "coefficients": {"x": 2.5},
            "methodology": "MLR+LASSO",
            "timestamp": "2023-01-01T00:00:00",
            "diagnostics": {
                "shapiro_wilk": {"stat": 0.9, "p": 0.5},
                "breusch_pagan": {"stat": 1.2, "p": 0.3}
            }
        }

        output_path = tmp_path / "analysis_results.json"
        # Patch get_data_path to return tmp_path
        with patch("analysis.get_data_path", return_value=output_path):
            save_analysis_results(results)

        assert output_path.exists()
        with open(output_path, "r") as f:
            saved_data = json.load(f)

        assert saved_data["status"] == "PASS"
        assert saved_data["R2"] == 0.85
        assert saved_data["diagnostics"]["shapiro_wilk"]["stat"] == 0.9