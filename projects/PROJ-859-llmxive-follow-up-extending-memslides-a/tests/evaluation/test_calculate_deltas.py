"""
Unit tests for code/evaluation/calculate_deltas.py
"""

import json
import csv
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.calculate_deltas import (
    DeltaCalculationError,
    load_benchmark_results,
    calculate_deltas,
    save_deltas,
    run_delta_calculation
)
from config import get_config, reset_config


class TestLoadBenchmarkResults:
    def test_load_valid_results(self, tmp_path):
        """Test loading valid benchmark results JSON."""
        # Create mock data
        mock_data = [
            {
                "trace_id": "trace_001",
                "edit_accuracy_baseline": 0.95,
                "edit_accuracy_compressed": 0.90,
                "latency_baseline": 1.2,
                "latency_compressed": 0.8
            },
            {
                "trace_id": "trace_002",
                "edit_accuracy_baseline": 0.88,
                "edit_accuracy_compressed": 0.85,
                "latency_baseline": 1.5,
                "latency_compressed": 0.9
            }
        ]
        
        results_file = tmp_path / "benchmark_results.json"
        with open(results_file, 'w') as f:
            json.dump(mock_data, f)
        
        config = {
            "benchmark_results_path": str(results_file)
        }
        
        results = load_benchmark_results(config)
        assert len(results) == 2
        assert results[0]["trace_id"] == "trace_001"
        assert results[1]["trace_id"] == "trace_002"

    def test_missing_file_raises_error(self, tmp_path):
        """Test that missing file raises DeltaCalculationError."""
        config = {
            "benchmark_results_path": str(tmp_path / "nonexistent.json")
        }
        
        with pytest.raises(DeltaCalculationError, match="not found"):
            load_benchmark_results(config)

    def test_invalid_json_raises_error(self, tmp_path):
        """Test that invalid JSON raises DeltaCalculationError."""
        results_file = tmp_path / "invalid.json"
        results_file.write_text("not valid json")
        
        config = {
            "benchmark_results_path": str(results_file)
        }
        
        with pytest.raises(DeltaCalculationError, match="parse benchmark results"):
            load_benchmark_results(config)


class TestCalculateDeltas:
    def test_calculate_correct_values(self):
        """Test delta calculation logic."""
        mock_results = [
            {
                "trace_id": "t1",
                "edit_accuracy_baseline": 1.0,
                "edit_accuracy_compressed": 0.8
            }
        ]
        
        deltas = calculate_deltas(mock_results)
        
        assert len(deltas) == 1
        assert deltas[0]["trace_id"] == "t1"
        assert deltas[0]["baseline_acc"] == 1.0
        assert deltas[0]["compressed_acc"] == 0.8
        assert deltas[0]["delta_acc"] == 0.2  # 1.0 - 0.8
        assert deltas[0]["fidelity_loss"] == 0.2  # 1 - 0.8

    def test_missing_trace_id_raises_error(self):
        """Test that missing trace_id raises error."""
        mock_results = [
            {
                "edit_accuracy_baseline": 1.0,
                "edit_accuracy_compressed": 0.8
            }
        ]
        
        with pytest.raises(DeltaCalculationError, match="Missing trace_id"):
            calculate_deltas(mock_results)

    def test_missing_accuracy_raises_error(self):
        """Test that missing accuracy metric raises error."""
        mock_results = [
            {
                "trace_id": "t1",
                "edit_accuracy_baseline": 1.0
                # missing compressed
            }
        ]
        
        with pytest.raises(DeltaCalculationError, match="Missing accuracy metric"):
            calculate_deltas(mock_results)

    def test_empty_results_raises_error(self):
        """Test that empty results list raises error."""
        with pytest.raises(DeltaCalculationError, match="No valid deltas"):
            calculate_deltas([])


class TestSaveDeltas:
    def test_save_creates_csv(self, tmp_path):
        """Test saving deltas creates valid CSV."""
        deltas = [
            {
                "trace_id": "t1",
                "baseline_acc": 1.0,
                "compressed_acc": 0.9,
                "delta_acc": 0.1,
                "fidelity_loss": 0.1
            }
        ]
        
        output_file = tmp_path / "deltas.csv"
        config = {
            "deltas_output_path": str(output_file)
        }
        
        result_path = save_deltas(deltas, config)
        
        assert result_path.exists()
        assert result_path.stat().st_size > 0
        
        # Verify content
        with open(result_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]["trace_id"] == "t1"
        assert float(rows[0]["delta_acc"]) == 0.1

    def test_creates_parent_directory(self, tmp_path):
        """Test that parent directories are created."""
        deltas = [
            {
                "trace_id": "t1",
                "baseline_acc": 1.0,
                "compressed_acc": 0.9,
                "delta_acc": 0.1,
                "fidelity_loss": 0.1
            }
        ]
        
        output_file = tmp_path / "subdir" / "deep" / "deltas.csv"
        config = {
            "deltas_output_path": str(output_file)
        }
        
        result_path = save_deltas(deltas, config)
        
        assert result_path.exists()


class TestRunDeltaCalculation:
    @patch('evaluation.calculate_deltas.load_benchmark_results')
    @patch('evaluation.calculate_deltas.save_deltas')
    def test_full_pipeline(self, mock_save, mock_load, tmp_path):
        """Test full pipeline execution."""
        # Setup mocks
        mock_load.return_value = [
            {
                "trace_id": "t1",
                "edit_accuracy_baseline": 1.0,
                "edit_accuracy_compressed": 0.9
            }
        ]
        mock_save.return_value = tmp_path / "deltas.csv"
        mock_save.return_value.parent.mkdir(parents=True, exist_ok=True)
        mock_save.return_value.touch() # Create empty file for existence check
        
        config = {
            "benchmark_results_path": str(tmp_path / "benchmark.json"),
            "deltas_output_path": str(tmp_path / "deltas.csv")
        }
        
        result = run_delta_calculation(config)
        
        assert mock_load.called
        assert mock_save.called
        assert result == tmp_path / "deltas.csv"

    @patch('evaluation.calculate_deltas.load_benchmark_results')
    def test_fails_on_load_error(self, mock_load, tmp_path):
        """Test pipeline fails if load fails."""
        mock_load.side_effect = DeltaCalculationError("Load failed")
        
        config = {
            "benchmark_results_path": str(tmp_path / "benchmark.json"),
            "deltas_output_path": str(tmp_path / "deltas.csv")
        }
        
        with pytest.raises(DeltaCalculationError, match="Load failed"):
            run_delta_calculation(config)