"""
Tests for the External Validation Proxy (T000).
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Adjust path to import code modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.validation_proxy import (
    load_json_data,
    extract_metric_values,
    run_ks_test,
    run_validation_proxy,
    PROXY_FILE_NAME
)
from config import get_config, reset_config


class TestValidationProxyHelpers:
    def test_load_json_data_list(self, tmp_path):
        data = [{"a": 1}, {"a": 2}]
        file_path = tmp_path / "test.json"
        file_path.write_text(json.dumps(data))
        assert load_json_data(file_path) == data

    def test_load_json_data_empty(self, tmp_path):
        file_path = tmp_path / "empty.json"
        file_path.write_text("[]")
        assert load_json_data(file_path) == []

    def test_load_json_data_missing(self, tmp_path):
        assert load_json_data(tmp_path / "nonexistent.json") == []

    def test_extract_metric_values(self):
        data = [
            {"sequence_entropy": 1.0, "other": "x"},
            {"sequence_entropy": 2.0},
            {"sequence_entropy": "invalid"}
        ]
        vals = extract_metric_values(data, "sequence_entropy")
        assert vals == [1.0, 2.0]

    def test_run_ks_test_insufficient_data(self):
        res = run_ks_test([1.0], [1.0, 2.0], "test")
        assert res["reason"] == "insufficient_data_points"
        assert res["ks_statistic"] is None

    def test_run_ks_test_valid(self):
        # Two clearly different distributions
        s1 = [1.0, 1.1, 1.2] * 10
        s2 = [10.0, 10.1, 10.2] * 10
        res = run_ks_test(s1, s2, "test")
        assert res["ks_statistic"] is not None
        assert res["p_value"] is not None
        assert res["is_significant_shift"] is True


class TestValidationProxyIntegration:
    @pytest.fixture
    def mock_config(self, tmp_path):
        # Setup a temporary config structure
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        training_dir = data_dir / "training"
        processed_dir.mkdir(parents=True)
        training_dir.mkdir()

        # Mock the config to use these paths
        config = MagicMock()
        config.DATA_DIR = str(data_dir)
        config.PROCESSED_DIR = str(processed_dir)
        return config, tmp_path

    def test_no_proxy_available(self, mock_config):
        config, tmp_path = mock_config
        with patch("analysis.validation_proxy.get_config", return_value=config):
            result = run_validation_proxy()
            assert result["status"] == "completed"
            assert result["proxy_found"] is False
            assert result["reason"] == "no_proxy_available"

            # Verify file was written
            output_file = Path(config.PROCESSED_DIR) / "validation_proxy.json"
            assert output_file.exists()
            with open(output_file) as f:
                written = json.load(f)
            assert written["reason"] == "no_proxy_available"

    def test_proxy_exists_no_synthetic(self, mock_config):
        config, tmp_path = mock_config
        # Create a proxy file
        proxy_path = Path(config.DATA_DIR) / PROXY_FILE_NAME
        proxy_path.write_text(json.dumps([{"sequence_entropy": 5.0}]))

        with patch("analysis.validation_proxy.get_config", return_value=config):
            result = run_validation_proxy()
            assert result["status"] == "completed"
            assert result["proxy_found"] is True
            assert result["reason"] == "synthetic_data_not_generated"

    def test_proxy_and_synthetic_exists(self, mock_config):
        config, tmp_path = mock_config
        # Create proxy
        proxy_path = Path(config.DATA_DIR) / PROXY_FILE_NAME
        proxy_path.write_text(json.dumps([{"sequence_entropy": 1.0} for _ in range(20)]))

        # Create synthetic training data
        synth_path = Path(config.DATA_DIR) / "training" / "trace_001.json"
        synth_path.write_text(json.dumps([{"sequence_entropy": 10.0} for _ in range(20)]))

        with patch("analysis.validation_proxy.get_config", return_value=config):
            result = run_validation_proxy()
            assert result["status"] == "completed"
            assert result["proxy_found"] is True
            assert "synthetic_data_not_generated" not in result
            assert "ks_tests" in result
            assert len(result["ks_tests"]) == 3 # All 3 metrics checked
            # Check if at least one is significant (they should be with 1.0 vs 10.0)
            assert result["is_valid_shift"] is True