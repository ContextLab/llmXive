"""Unit tests for preprocessing.scaling (T003, FR-002)."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import preprocessing.scaling as scaling
from preprocessing.scaling import (
    min_max_scale,
    robust_scale,
    standardize,
    standardize_data,
)


@pytest.fixture
def rng():
    return np.random.default_rng(42)


class TestStandardize:
    def test_mean_zero_std_one(self, rng):
        x = rng.normal(loc=5.0, scale=3.0, size=500)
        out = standardize(x)
        assert np.abs(np.mean(out)) < 1e-5
        assert np.abs(np.std(out) - 1.0) < 1e-5

    def test_dataframe_columns(self, rng):
        df = pd.DataFrame(
            {
                "a": rng.normal(10, 2, 300),
                "b": rng.normal(-4, 7, 300),
            }
        )
        out = standardize(df)
        assert np.all(np.abs(out.mean().to_numpy()) < 1e-5)
        assert np.all(np.abs(out.std().to_numpy() - 1.0) < 1e-5)

    def test_constant_data_no_nan(self):
        out = standardize(np.full(50, 3.14))
        assert np.all(np.isfinite(out))
        assert np.all(out == 0.0)

    def test_legacy_alias(self, rng):
        x = rng.normal(size=100)
        assert np.allclose(standardize_data(x), standardize(x))

    def test_pvalue_invariance(self, rng):
        """Scaling must not alter t-test p-values (spec US-2)."""
        from scipy import stats

        g1 = rng.normal(0, 1, 200)
        g2 = rng.normal(0.5, 1, 200)
        p_raw = stats.ttest_ind(g1, g2).pvalue
        p_scaled = stats.ttest_ind(
            standardize(g1, persist=False), standardize(g2, persist=False)
        ).pvalue
        assert abs(p_raw - p_scaled) < 1e-4


class TestMinMax:
    def test_min_zero_max_one(self, rng):
        x = rng.uniform(-20, 130, 400)
        out = min_max_scale(x)
        assert np.isclose(np.min(out), 0.0)
        assert np.isclose(np.max(out), 1.0)

    def test_dataframe(self, rng):
        df = pd.DataFrame(
            {"a": rng.uniform(-5, 5, 200), "b": rng.uniform(100, 900, 200)}
        )
        out = min_max_scale(df)
        assert np.allclose(out.min().to_numpy(), 0.0)
        assert np.allclose(out.max().to_numpy(), 1.0)

    def test_constant_data_maps_to_min_val(self):
        out = min_max_scale(np.full(20, 7.0))
        assert np.all(np.isfinite(out))
        assert np.all(out == 0.0)

    def test_invalid_range_raises(self, rng):
        x = rng.normal(size=50)
        with pytest.raises(ValueError):
            min_max_scale(x, min_val=1.0, max_val=0.0)


class TestRobust:
    def test_basic_properties(self, rng):
        x = rng.normal(loc=2, scale=5, size=600)
        out = robust_scale(x)
        assert np.all(np.isfinite(out))
        assert np.abs(np.median(out)) < 1e-10

    def test_zero_iqr_no_nan(self):
        """Constant data (zero IQR) must not produce NaNs (edge case)."""
        out = robust_scale(np.full(100, 42.0))
        assert np.all(np.isfinite(out))
        assert np.all(out == 0.0)

    def test_dataframe_zero_iqr_column(self, rng):
        df = pd.DataFrame(
            {"a": rng.normal(size=100), "b": np.full(100, 5.0)}
        )
        out = robust_scale(df)
        assert not out.isnull().any().any()
        assert np.all(out["b"].to_numpy() == 0.0)

    def test_outliers_no_nan(self, rng):
        x = np.concatenate([rng.normal(size=100), [1e12, -1e12]])
        out = robust_scale(x)
        assert np.all(np.isfinite(out))


class TestInvalidInput:
    def test_none_raises(self):
        for fn in (standardize, min_max_scale, robust_scale):
            with pytest.raises(ValueError):
                fn(None)

    def test_empty_raises(self):
        for fn in (standardize, min_max_scale, robust_scale):
            with pytest.raises(ValueError):
                fn(np.array([]))

    def test_non_numeric_raises(self):
        for fn in (standardize, min_max_scale, robust_scale):
            with pytest.raises(ValueError):
                fn(["a", "b", "c"])

    def test_nan_raises(self):
        for fn in (standardize, min_max_scale, robust_scale):
            with pytest.raises(ValueError):
                fn(np.array([1.0, np.nan, 3.0]))

    def test_non_numeric_dataframe_raises(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        for fn in (standardize, min_max_scale, robust_scale):
            with pytest.raises(ValueError):
                fn(df)


class TestLoggingAndPreservation:
    def test_prescaled_copy_and_log_written(self, rng, monkeypatch, tmp_path):
        monkeypatch.setattr(scaling, "PRE_SCALED_DIR", tmp_path / "pre_scaled")
        monkeypatch.setattr(scaling, "LOGS_DIR", tmp_path / "logs")

        df = pd.DataFrame({"a": rng.normal(size=50)})
        original = df.copy()
        standardize(df)

        copies = list((tmp_path / "pre_scaled" / "standardize").glob("original_*.csv"))
        assert len(copies) == 1
        saved = pd.read_csv(copies[0])
        pd.testing.assert_frame_equal(saved, original)

        log_file = tmp_path / "logs" / "scaling_standardize.log"
        assert log_file.exists()
        lines = [
            json.loads(line)
            for line in log_file.read_text().strip().splitlines()
        ]
        assert len(lines) == 1
        entry = lines[0]
        assert entry["method"] == "standardize"
        assert "timestamp" in entry
        assert "parameters" in entry
        assert entry["preserved_copy"] == str(copies[0])

    def test_minmax_log_includes_parameters(self, rng, monkeypatch, tmp_path):
        monkeypatch.setattr(scaling, "PRE_SCALED_DIR", tmp_path / "pre_scaled")
        monkeypatch.setattr(scaling, "LOGS_DIR", tmp_path / "logs")

        min_max_scale(rng.normal(size=30), min_val=-1.0, max_val=2.0)

        log_file = tmp_path / "logs" / "scaling_minmax.log"
        entry = json.loads(log_file.read_text().strip().splitlines()[0])
        assert entry["method"] == "minmax"
        assert entry["parameters"] == {"min_val": -1.0, "max_val": 2.0}

    def test_robust_prescaled_copy(self, rng, monkeypatch, tmp_path):
        monkeypatch.setattr(scaling, "PRE_SCALED_DIR", tmp_path / "pre_scaled")
        monkeypatch.setattr(scaling, "LOGS_DIR", tmp_path / "logs")

        x = rng.normal(size=40)
        robust_scale(x)
        copies = list((tmp_path / "pre_scaled" / "robust").glob("original_*.csv"))
        assert len(copies) == 1

    def test_persist_false_skips_io(self, rng, monkeypatch, tmp_path):
        monkeypatch.setattr(scaling, "PRE_SCALED_DIR", tmp_path / "pre_scaled")
        monkeypatch.setattr(scaling, "LOGS_DIR", tmp_path / "logs")
        standardize(rng.normal(size=20), persist=False)
        assert not (tmp_path / "pre_scaled").exists()
        assert not (tmp_path / "logs").exists()
