"""Tests for the base configuration and logging infrastructure (T006)."""
import json
import logging
import sys
from pathlib import Path

import pytest

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from utils.config import Config, get_config, reset_config, load_config_from_env  # noqa: E402
from utils.logger import setup_logger, get_logger  # noqa: E402
from utils.stats_aggregator import (  # noqa: E402
    calculate_stability_metrics,
    aggregate_from_profiles,
    save_stability_report,
)


@pytest.fixture(autouse=True)
def _reset_config():
    reset_config()
    yield
    reset_config()


class TestConfig:
    def test_singleton(self):
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_defaults(self):
        cfg = get_config()
        assert cfg.window_size_days == 30
        assert cfg.r2_threshold == 0.8
        assert cfg.random_seed == 42
        assert cfg.n_estimators == 100
        assert cfg.max_depth == 10
        assert cfg.target_col == "load"

    def test_mapping_get(self):
        cfg = get_config()
        assert cfg.get("window_size_days") == 30
        assert cfg.get("missing_key", "fallback") == "fallback"
        assert cfg["target_col"] == "load"
        assert "r2_threshold" in cfg

    def test_directories_exist_as_paths(self):
        cfg = get_config()
        assert cfg.project_root.is_dir()
        assert cfg.project_root == Config().project_root
        assert cfg.data_dir.name == "data"
        assert cfg.outputs_dir.name == "outputs"

    def test_paths_section(self):
        cfg = get_config()
        paths = cfg.get("paths")
        assert "importance_profiles" in paths
        assert "drift_metrics" in paths
        assert paths["global_stats"].endswith("global_stats.json")

    def test_json_overrides(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"r2_threshold": 0.9, "target_col": "y"}))
        cfg = get_config(str(cfg_file))
        assert cfg.get("r2_threshold") == 0.9
        assert cfg.get("target_col") == "y"
        # Non-overridden defaults remain
        assert cfg.get("window_size_days") == 30

    def test_missing_json_file_keeps_defaults(self, tmp_path):
        cfg = get_config(str(tmp_path / "nope.json"))
        assert cfg.get("r2_threshold") == 0.8

    def test_env_overrides(self, monkeypatch):
        monkeypatch.setenv("FID_R2_THRESHOLD", "0.75")
        monkeypatch.setenv("FID_TARGET_COL", "demand")
        get_config()  # instantiate singleton
        overrides = load_config_from_env()
        assert overrides["r2_threshold"] == 0.75
        assert overrides["target_col"] == "demand"
        assert get_config().get("r2_threshold") == 0.75

    def test_reset(self):
        c1 = get_config()
        reset_config()
        c2 = get_config()
        assert c1 is not c2

    def test_to_dict_roundtrip(self):
        d = get_config().to_dict()
        assert isinstance(d, dict)
        assert d["window_size_days"] == 30


class TestLogger:
    def test_get_logger_returns_logger(self):
        log = get_logger("test_module_a")
        assert isinstance(log, logging.Logger)
        assert log.name == "test_module_a"
        assert log.level == logging.INFO

    def test_setup_logger_idempotent(self):
        log1 = setup_logger("test_module_b")
        n_handlers = len(log1.handlers)
        log2 = setup_logger("test_module_b")
        assert log1 is log2
        assert len(log2.handlers) == n_handlers

    def test_file_handler(self, tmp_path):
        log_file = tmp_path / "logs" / "run.log"
        log = setup_logger("test_file_logger", log_file=str(log_file))
        log.info("hello from file logger")
        for h in log.handlers:
            h.flush()
        assert log_file.exists()
        assert "hello from file logger" in log_file.read_text()
        # Clean up handlers so other tests are not affected
        for h in list(log.handlers):
            log.removeHandler(h)


class TestStatsAggregator:
    def test_empty(self):
        metrics = calculate_stability_metrics([])
        assert metrics == {
            "total_windows": 0,
            "stable_window_count": 0,
            "average_r_squared": 0.0,
        }

    def test_stable_counts(self):
        profiles = [
            {"window_id": "W001", "r_squared": 0.9},
            {"window_id": "W002", "r_squared": 0.85},
            {"window_id": "W003", "r_squared": 0.5},
        ]
        metrics = calculate_stability_metrics(profiles)
        assert metrics["total_windows"] == 3
        assert metrics["stable_window_count"] == 2
        assert metrics["average_r_squared"] == pytest.approx((0.9 + 0.85 + 0.5) / 3)

    def test_custom_threshold(self):
        profiles = [{"r_squared": 0.7}]
        metrics = calculate_stability_metrics(profiles, r2_threshold=0.6)
        assert metrics["stable_window_count"] == 1

    def test_profiles_without_r2(self):
        profiles = [{"window_id": "W001"}, {"window_id": "W002"}]
        metrics = calculate_stability_metrics(profiles)
        assert metrics["stable_window_count"] == 2
        assert metrics["average_r_squared"] == 0.0

    def test_aggregate_from_directory(self, tmp_path):
        for i, r2 in enumerate([0.9, 0.6]):
            p = tmp_path / f"importance_profile_W00{i}.json"
            p.write_text(json.dumps({"window_id": f"W00{i}", "r_squared": r2}))
        metrics = aggregate_from_profiles(tmp_path)
        assert metrics["total_windows"] == 2
        assert metrics["stable_window_count"] == 1

    def test_aggregate_missing_path(self, tmp_path):
        metrics = aggregate_from_profiles(tmp_path / "does_not_exist")
        assert metrics["total_windows"] == 0

    def test_save_stability_report(self, tmp_path):
        metrics = calculate_stability_metrics([{"r_squared": 0.9}])
        out = tmp_path / "sub" / "stability_report.json"
        save_stability_report(metrics, out)
        assert out.exists()
        loaded = json.loads(out.read_text())
        assert loaded["stable_window_count"] == 1