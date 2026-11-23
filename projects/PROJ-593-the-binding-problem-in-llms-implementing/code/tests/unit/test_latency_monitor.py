import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Mock torch and transformers to avoid heavy imports in unit tests
# We are testing the logic of the latency monitor functions, not the model itself
from unittest.mock import MagicMock, patch, mock_open

@pytest.fixture
def mock_model():
    model = MagicMock()
    model.to = MagicMock(return_value=model)
    model.eval = MagicMock()
    model.forward = MagicMock(return_value={"last_hidden_state": MagicMock()})
    return model

@pytest.fixture
def mock_tokenizer():
    tokenizer = MagicMock()
    # Return mock input_ids with varying lengths
    tokenizer.return_value = {
        "input_ids": [[101, 2000, 2001, 102], [101, 2000, 2001, 2002, 102]]
    }
    return tokenizer

class TestLatencyBudgetCheck:
    def test_within_budget(self):
        from src.analysis.latency_monitor import check_latency_budget

        metrics = {
            "total_time_seconds": 10.0,
            "avg_time_per_token_seconds": 0.020, # 20ms
            "total_tokens_processed": 100,
            "num_batches": 2,
            "measurement_runs": 5
        }
        
        result = check_latency_budget(metrics, max_total_seconds=300.0, max_time_per_token_ms=25.0)
        
        assert result["within_total_budget"] is True
        assert result["within_token_budget"] is True
        assert result["passed"] is True
        assert result["actual_avg_time_per_token_ms"] == 20.0

    def test_exceeds_total_budget(self):
        from src.analysis.latency_monitor import check_latency_budget

        metrics = {
            "total_time_seconds": 350.0,
            "avg_time_per_token_seconds": 0.020,
            "total_tokens_processed": 100,
            "num_batches": 2,
            "measurement_runs": 5
        }
        
        result = check_latency_budget(metrics, max_total_seconds=300.0, max_time_per_token_ms=25.0)
        
        assert result["within_total_budget"] is False
        assert result["within_token_budget"] is True
        assert result["passed"] is False

    def test_exceeds_token_budget(self):
        from src.analysis.latency_monitor import check_latency_budget

        metrics = {
            "total_time_seconds": 10.0,
            "avg_time_per_token_seconds": 0.030, # 30ms
            "total_tokens_processed": 100,
            "num_batches": 2,
            "measurement_runs": 5
        }
        
        result = check_latency_budget(metrics, max_total_seconds=300.0, max_time_per_token_ms=25.0)
        
        assert result["within_total_budget"] is True
        assert result["within_token_budget"] is False
        assert result["passed"] is False

class TestLatencyAnalysis:
    @patch("src.analysis.latency_measure_forward_pass_latency")
    @patch("src.analysis.latency_monitor.load_distilbert_cpu")
    @patch("src.analysis.latency_monitor.OscillatoryDistilBERTWrapper")
    @patch("src.analysis.latency_monitor.DistilBertTokenizerFast.from_pretrained")
    def test_run_latency_analysis_saves_file(
        self, 
        mock_tokenizer_from_pretrained, 
        mock_osc_wrapper, 
        mock_load_cpu, 
        mock_measure
    ):
        from src.analysis.latency_monitor import run_latency_analysis

        # Setup mocks
        mock_tokenizer = MagicMock()
        mock_tokenizer_from_pretrained.return_value = mock_tokenizer
        
        mock_base_model = MagicMock()
        mock_load_cpu.return_value = MagicMock(model=mock_base_model)
        
        mock_osc_model = MagicMock()
        mock_osc_wrapper.return_value = MagicMock(model=mock_osc_model)
        
        mock_measure.return_value = {
            "total_time_seconds": 50.0,
            "avg_time_per_batch_seconds": 10.0,
            "avg_time_per_token_seconds": 0.020,
            "total_tokens_processed": 500,
            "num_batches": 5,
            "measurement_runs": 5
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "latency_report.json")
            texts = ["Test sentence one.", "Test sentence two."]
            
            report = run_latency_analysis(
                texts=texts,
                output_path=output_path,
                device="cpu",
                frequency=40.0,
                use_oscillation=True
            )
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify content
            with open(output_path, "r") as f:
                saved_report = json.load(f)
            
            assert saved_report["model_type"] == "OscillatoryDistilBERT"
            assert saved_report["frequency_cycles_per_sequence"] == 40.0
            assert saved_report["budget_check"]["passed"] is True
            assert "timestamp" in saved_report

    @patch("src.analysis.latency_monitor.measure_forward_pass_latency")
    @patch("src.analysis.latency_monitor.load_distilbert_cpu")
    @patch("src.analysis.latency_monitor.DistilBertTokenizerFast.from_pretrained")
    def test_baseline_latency_analysis(
        self, 
        mock_tokenizer_from_pretrained, 
        mock_load_cpu, 
        mock_measure
    ):
        from src.analysis.latency_monitor import run_latency_analysis

        mock_tokenizer = MagicMock()
        mock_tokenizer_from_pretrained.return_value = mock_tokenizer
        
        mock_wrapper = MagicMock()
        mock_load_cpu.return_value = mock_wrapper
        
        mock_measure.return_value = {
            "total_time_seconds": 30.0,
            "avg_time_per_batch_seconds": 6.0,
            "avg_time_per_token_seconds": 0.015,
            "total_tokens_processed": 400,
            "num_batches": 5,
            "measurement_runs": 5
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "baseline_latency.json")
            texts = ["Test."]
            
            report = run_latency_analysis(
                texts=texts,
                output_path=output_path,
                device="cpu",
                use_oscillation=False
            )
            
            assert os.path.exists(output_path)
            
            with open(output_path, "r") as f:
                saved_report = json.load(f)
            
            assert saved_report["model_type"] == "DistilBERTBaseline"
            assert saved_report["frequency_cycles_per_sequence"] is None
            assert saved_report["budget_check"]["passed"] is True