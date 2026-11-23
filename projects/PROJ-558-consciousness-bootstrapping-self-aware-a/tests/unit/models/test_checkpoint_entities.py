import json
import tempfile
from pathlib import Path
from datetime import datetime
import pytest

from code.models.checkpoint import ModelCheckpoint
from code.evaluation.results import EvaluationResult


class TestModelCheckpoint:
    def test_creation(self):
        """Test basic creation of ModelCheckpoint."""
        checkpoint = ModelCheckpoint(
            checkpoint_id="test-001",
            model_type="recursive",
            architecture="TinyLlama-1.1B",
            recursion_depth=2,
            epoch=5,
            step=1000,
            loss=0.45,
            metrics={"accuracy": 0.85},
            tags=["final", "best"]
        )
        assert checkpoint.checkpoint_id == "test-001"
        assert checkpoint.loss == 0.45
        assert "best" in checkpoint.tags

    def test_to_dict_serialization(self):
        """Test conversion to dictionary."""
        checkpoint = ModelCheckpoint(
            checkpoint_id="test-002",
            model_type="baseline",
            architecture="TinyLlama-1.1B",
            recursion_depth=0,
            epoch=10,
            step=2000,
            loss=0.30,
            metrics={"accuracy": 0.90, "loss": 0.30}
        )
        data = checkpoint.to_dict()
        assert isinstance(data, dict)
        assert data["checkpoint_id"] == "test-002"
        assert data["loss"] == 0.30
        assert "created_at" in data

    def test_to_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        checkpoint = ModelCheckpoint(
            checkpoint_id="test-003",
            model_type="recursive",
            architecture="TinyLlama-1.1B",
            recursion_depth=1,
            epoch=3,
            step=500,
            loss=0.55
        )
        json_str = checkpoint.to_json()
        assert isinstance(json_str, str)
        
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed["checkpoint_id"] == "test-003"

    def test_save_and_load_metadata(self):
        """Test saving to file and loading back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint = ModelCheckpoint(
                checkpoint_id="test-004",
                model_type="recursive",
                architecture="TinyLlama-1.1B",
                recursion_depth=2,
                epoch=1,
                step=100,
                loss=0.60,
                metrics={"proxy_loss": 0.15}
            )
            
            saved_path = checkpoint.save_metadata(tmpdir)
            assert saved_path.exists()
            
            loaded = ModelCheckpoint.load_metadata(str(saved_path))
            assert loaded.checkpoint_id == checkpoint.checkpoint_id
            assert loaded.loss == checkpoint.loss
            assert loaded.metrics == checkpoint.metrics

    def test_from_dict_with_datetime(self):
        """Test from_dict handles datetime correctly."""
        data = {
            "checkpoint_id": "test-005",
            "model_type": "baseline",
            "architecture": "TinyLlama-1.1B",
            "recursion_depth": 0,
            "epoch": 1,
            "step": 10,
            "loss": 0.70,
            "created_at": datetime(2026, 1, 1, 12, 0, 0).isoformat()
        }
        checkpoint = ModelCheckpoint.from_dict(data)
        assert isinstance(checkpoint.created_at, datetime)
        assert checkpoint.created_at.year == 2026


class TestEvaluationResult:
    def test_creation(self):
        """Test basic creation of EvaluationResult."""
        result = EvaluationResult(
            evaluation_id="eval-001",
            model_checkpoint_id="ckpt-001",
            benchmark_name="gsm8k_self_consistency",
            dataset_name="gsm8k",
            num_samples=100,
            metrics={"accuracy": 0.75, "brier_score": 0.12},
            self_consistency_score=0.82
        )
        assert result.evaluation_id == "eval-001"
        assert result.self_consistency_score == 0.82

    def test_to_dict_serialization(self):
        """Test conversion to dictionary."""
        result = EvaluationResult(
            evaluation_id="eval-002",
            model_checkpoint_id="ckpt-002",
            benchmark_name="mmlu_standard",
            dataset_name="mmlu",
            num_samples=50,
            metrics={"accuracy": 0.65}
        )
        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["evaluation_id"] == "eval-002"
        assert data["num_samples"] == 50

    def test_to_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        result = EvaluationResult(
            evaluation_id="eval-003",
            model_checkpoint_id="ckpt-003",
            benchmark_name="gsm8k_self_consistency",
            dataset_name="gsm8k",
            num_samples=200,
            metrics={"accuracy": 0.80, "roc_auc": 0.88},
            calibration_metrics={"ece": 0.05, "brier": 0.10}
        )
        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert parsed["evaluation_id"] == "eval-003"
        assert "calibration_metrics" in parsed

    def test_save_and_load_file(self):
        """Test saving to file and loading back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = EvaluationResult(
                evaluation_id="eval-004",
                model_checkpoint_id="ckpt-004",
                benchmark_name="gsm8k_self_consistency",
                dataset_name="gsm8k",
                num_samples=150,
                metrics={"accuracy": 0.72, "self_consistency": 0.78}
            )
            
            output_path = Path(tmpdir) / "results" / "eval_004.json"
            saved_path = result.save_to_file(str(output_path))
            assert saved_path.exists()
            
            loaded = EvaluationResult.load_from_file(str(saved_path))
            assert loaded.evaluation_id == result.evaluation_id
            assert loaded.metrics == result.metrics

    def test_from_dict_with_datetime(self):
        """Test from_dict handles datetime correctly."""
        data = {
            "evaluation_id": "eval-005",
            "model_checkpoint_id": "ckpt-005",
            "benchmark_name": "test_bench",
            "dataset_name": "test_data",
            "num_samples": 10,
            "created_at": datetime(2026, 5, 25, 10, 30, 0).isoformat()
        }
        result = EvaluationResult.from_dict(data)
        assert isinstance(result.created_at, datetime)
        assert result.created_at.month == 5