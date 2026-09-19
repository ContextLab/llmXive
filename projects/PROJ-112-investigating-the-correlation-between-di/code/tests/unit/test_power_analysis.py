"""
Unit tests for the power_analysis module.
"""
import pytest
import math
import tempfile
import os
from pathlib import Path
import pandas as pd
import numpy as np

from src.utils.power_analysis import (
    calculate_effect_size,
    calculate_power_spearman,
    calculate_margin_of_error,
    run_power_analysis
)


class TestEffectSize:
    def test_r_squared_calculation(self):
        r = 0.5
        result = calculate_effect_size(r, 100)
        assert abs(result["r_squared"] - 0.25) < 1e-6

    def test_fisher_z_transformation(self):
        r = 0.0
        result = calculate_effect_size(r, 100)
        assert abs(result["fisher_z"]) < 1e-6

        r = 0.5
        expected_z = 0.5 * math.log((1 + 0.5) / (1 - 0.5))
        result = calculate_effect_size(r, 100)
        assert abs(result["fisher_z"] - expected_z) < 1e-4

    def test_confidence_interval_bounds(self):
        r = 0.5
        n = 100
        result = calculate_effect_size(r, n)
        assert result["ci_lower_95"] < r
        assert result["ci_upper_95"] > r
        assert result["ci_lower_95"] < result["ci_upper_95"]


class TestPowerSpearman:
    def test_power_increases_with_n(self):
        rho = 0.5
        power_50 = calculate_power_spearman(50, rho)
        power_100 = calculate_power_spearman(100, rho)
        assert power_100 > power_50

    def test_power_increases_with_rho(self):
        n = 100
        power_05 = calculate_power_spearman(n, 0.5)
        power_08 = calculate_power_spearman(n, 0.8)
        assert power_08 > power_05

    def test_power_near_zero(self):
        n = 100
        power = calculate_power_spearman(n, 0.0)
        # Power should be close to alpha (0.05) when rho is 0
        assert power < 0.1

    def test_power_with_large_sample(self):
        n = 1000
        rho = 0.3
        power = calculate_power_spearman(n, rho)
        assert power > 0.9


class TestMarginOfError:
    def test_margin_decreases_with_n(self):
        me_50 = calculate_margin_of_error(50)
        me_100 = calculate_margin_of_error(100)
        assert me_100 < me_50

    def test_margin_positive(self):
        me = calculate_margin_of_error(50)
        assert me > 0

    def test_margin_small_for_large_n(self):
        me = calculate_margin_of_error(10000)
        assert me < 0.1


class TestRunPowerAnalysis:
    @pytest.fixture
    def temp_csv_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create synthetic data with known correlation
            np.random.seed(42)
            n = 100
            x = np.random.normal(0, 1, n)
            y = 0.5 * x + np.random.normal(0, 0.5, n)  # rho approx 0.5
            df = pd.DataFrame({"fiber_intake": x, "taxon_abundance": y})
            df.to_csv(f.name, index=False)
            yield Path(f.name)
            os.unlink(f.name)

    @pytest.fixture
    def temp_tsv_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            np.random.seed(42)
            n = 100
            x = np.random.normal(0, 1, n)
            y = 0.5 * x + np.random.normal(0, 0.5, n)
            df = pd.DataFrame({"fiber_intake": x, "taxon_abundance": y})
            df.to_csv(f.name, sep='\t', index=False)
            yield Path(f.name)
            os.unlink(f.name)

    def test_run_power_analysis_csv(self, temp_csv_file):
        with tempfile.NamedTemporaryFile(suffix='.tsv', delete=False) as out_f:
            out_path = Path(out_f.name)
        
        try:
            results = run_power_analysis(
                input_file=temp_csv_file,
                output_file=out_path,
                fiber_col="fiber_intake",
                taxa_col="taxon_abundance"
            )
            
            assert "statistical_power" in results
            assert results["statistical_power"] > 0
            assert results["observed_rho"] != 0.0 # Should be around 0.5
            assert out_path.exists()
        finally:
            if out_path.exists():
                os.unlink(out_path)

    def test_run_power_analysis_tsv(self, temp_tsv_file):
        with tempfile.NamedTemporaryFile(suffix='.tsv', delete=False) as out_f:
            out_path = Path(out_f.name)
        
        try:
            results = run_power_analysis(
                input_file=temp_tsv_file,
                output_file=out_path,
                fiber_col="fiber_intake",
                taxa_col="taxon_abundance"
            )
            
            assert "statistical_power" in results
            assert out_path.exists()
        finally:
            if out_path.exists():
                os.unlink(out_path)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            run_power_analysis(
                input_file=Path("nonexistent.csv"),
                output_file=Path("output.tsv")
            )

    def test_missing_column(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
            df.to_csv(f.name, index=False)
            path = Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                run_power_analysis(
                    input_file=path,
                    output_file=Path("out.tsv"),
                    fiber_col="nonexistent"
                )
        finally:
            os.unlink(path)