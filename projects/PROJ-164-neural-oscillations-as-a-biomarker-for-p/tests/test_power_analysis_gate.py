"""Unit tests for the T009 power analysis gate."""
import importlib.util
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT_ROOT / "code" / "09_power_analysis_gate.py"

spec = importlib.util.spec_from_file_location(
    "power_analysis_gate", MODULE_PATH
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestMinimumSampleSize:
    def test_returns_int_above_predictors(self):
        n = mod.calculate_minimum_sample_size(
            r2_target=0.1, power=0.8, alpha=0.05, k_predictors=21
        )
        assert isinstance(n, int)
        assert n > 21

    def test_power_achieved_at_n_min(self):
        n = mod.calculate_minimum_sample_size(
            r2_target=0.1, power=0.8, alpha=0.05, k_predictors=21
        )
        pw = mod.achieved_power_at_n(n, 0.1, 0.05, 21)
        assert pw >= 0.8

    def test_power_below_n_min(self):
        n = mod.calculate_minimum_sample_size(
            r2_target=0.1, power=0.8, alpha=0.05, k_predictors=21
        )
        pw = mod.achieved_power_at_n(n - 1, 0.1, 0.05, 21)
        assert pw < 0.8

    def test_invalid_r2_raises(self):
        with pytest.raises(ValueError):
            mod.calculate_minimum_sample_size(r2_target=1.5)

    def test_invalid_power_raises(self):
        with pytest.raises(ValueError):
            mod.calculate_minimum_sample_size(power=1.5)


class TestGate:
    def test_underpowered_when_small_n(self):
        manifest = {
            "status": "found",
            "paired_found": True,
            "N_actual": 20,
            "mode_flag": "Primary",
            "dataset": {"predictor_count": 21},
        }
        report = mod.run_gate(manifest, None)
        assert report["mode_flag"] == "Underpowered"
        assert report["inference_allowed"] is False
        assert report["N_actual"] < report["N_min"]
        assert report["fr005_flag"]["status"] == "underpowered"

    def test_sufficient_power_when_large_n(self):
        manifest = {
            "status": "found",
            "paired_found": True,
            "N_actual": 1000,
            "mode_flag": "Primary",
            "dataset": {"predictor_count": 21},
        }
        report = mod.run_gate(manifest, None)
        assert report["mode_flag"] == "Primary"
        assert report["inference_allowed"] is True
        assert report["status"] == "Sufficient Power"

    def test_data_insufficient_preserved(self):
        manifest = {
            "status": "No single-source paired dataset found",
            "mode_flag": "Data Insufficient",
            "N_actual": 0,
        }
        report = mod.run_gate(manifest, None)
        assert report["mode_flag"] == "Data Insufficient"
        assert report["inference_allowed"] is False

    def test_prereg_updated_with_actual_k_when_found(self):
        manifest = {
            "status": "found",
            "paired_found": True,
            "N_actual": 500,
            "mode_flag": "Primary",
            "dataset": {"predictor_count": 25},
        }
        report = mod.run_gate(manifest, None)
        updated = mod.update_preregistration(
            {"parameters": {}}, report
        )
        assert updated["parameters"]["k_predictors"] == 25
        assert updated["k_predictors_status"] == "actual"

    def test_prereg_placeholder_retained_when_absent(self):
        manifest = {"status": "absent", "mode_flag": "Data Insufficient"}
        report = mod.run_gate(manifest, None)
        updated = mod.update_preregistration(
            {"parameters": {"k_predictors": None}}, report
        )
        assert updated["parameters"]["k_predictors"] is None
        assert updated["k_predictors_status"] == "placeholder"

    def test_missing_manifest_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            mod.load_manifest(tmp_path / "nope.json")