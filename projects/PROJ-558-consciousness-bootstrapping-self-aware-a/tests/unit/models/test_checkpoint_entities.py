import pytest
from datetime import datetime
from pathlib import Path
import json
import tempfile
import os

# Import the entities created in T006
from code.models.checkpoint import ModelCheckpoint
from code.evaluation.results import EvaluationResult

class TestModelCheckpoint:
    def test_creation_and_defaults(self):
        """Test that a checkpoint can be created with defaults."""
        ckpt = ModelCheckpoint(
            checkpoint_id="test-001",
            model_type="recursive_llama"
        )
        assert ckpt.checkpoint_id == "test-001"
        assert ckpt.model_type == "recursive_llama"
        assert ckpt.epoch == 0
        assert ckpt.loss is None
        assert isinstance(ckpt.timestamp, datetime)

    def test_to_dict_serialization(self):
        """Test conversion to dictionary."""
        ckpt = ModelCheckpoint(
            checkpoint_id="test-002",
            model_type="baseline_llama",
            epoch=5,
            loss=0.42,
            metrics={"accuracy": 0.85}
        )
        data = ckpt.to_dict()
        assert data["checkpoint_id"] == "test-002"
        assert data["epoch"] == 5
        assert data["loss"] == 0.42
        assert data["metrics"]["accuracy"] == 0.85
        assert "timestamp" in data

    def test_from_dict_deserialization(self):
        """Test reconstruction from dictionary."""
        raw_data = {
            "checkpoint_id": "test-003",
            "model_type": "recursive_llama",
            "epoch": 10,
            "step": 1000,
            "loss": 0.1,
            "metrics": {"loss": 0.1},
            "timestamp": datetime.now().isoformat()
        }
        ckpt = ModelCheckpoint.from_dict(raw_data)
        assert ckpt.checkpoint_id == "test-003"
        assert ckpt.epoch == 10
        assert ckpt.loss == 0.1

    def test_save_and_load_metadata(self):
        """Test saving metadata to disk and reloading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            ckpt = ModelCheckpoint(
                checkpoint_id="test-004",
                model_type="recursive_llama",
                epoch=1,
                metrics={"val_acc": 0.9}
            )
            ckpt.save_metadata(output_dir)
            
            metadata_file = output_dir / "test-004_metadata.json"
            assert metadata_file.exists()
            
            with open(metadata_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data["checkpoint_id"] == "test-004"
            assert loaded_data["metrics"]["val_acc"] == 0.9

class TestEvaluationResult:
    def test_creation_with_paths(self):
        """Test creation with generated paths."""
        result = EvaluationResult(
            result_id="eval-001",
            dataset_name="gsm8k",
            question_id="q-123",
            generated_paths=["Answer: 5", "Answer: 5", "Answer: 4"],
            majority_vote_answer="5",
            confidence_scores=[0.9, 0.8, 0.6],
            average_confidence=0.76,
            ground_truth="5",
            is_correct=True
        )
        assert result.result_id == "eval-001"
        assert len(result.generated_paths) == 3
        assert result.is_correct is True

    def test_serialization(self):
        """Test full serialization to dict."""
        result = EvaluationResult(
            result_id="eval-002",
            dataset_name="mmlu",
            question_id="q-999",
            generated_paths=["Option A"],
            majority_vote_answer="A",
            confidence_scores=[0.5],
            average_confidence=0.5,
            ground_truth="B",
            is_correct=False,
            metrics={"consistency": 1.0}
        )
        data = result.to_dict()
        assert data["dataset_name"] == "mmlu"
        assert data["is_correct"] is False
        assert data["metrics"]["consistency"] == 1.0

    def test_deserialization(self):
        """Test reconstruction from dict."""
        raw = {
            "result_id": "eval-003",
            "dataset_name": "gsm8k",
            "question_id": "q-55",
            "timestamp": datetime.now().isoformat(),
            "generated_paths": ["5", "5"],
            "majority_vote_answer": "5",
            "tie_break_used": False,
            "confidence_scores": [0.8, 0.8],
            "average_confidence": 0.8,
            "ground_truth": "5",
            "is_correct": True,
            "metrics": {},
            "raw_log_data": {}
        }
        result = EvaluationResult.from_dict(raw)
        assert result.result_id == "eval-003"
        assert result.is_correct is True

    def test_save_to_json(self):
        """Test saving result to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "result.json"
            result = EvaluationResult(
                result_id="eval-004",
                dataset_name="gsm8k",
                question_id="q-1",
                generated_paths=["10"],
                majority_vote_answer="10",
                ground_truth="10",
                is_correct=True
            )
            result.save_to_json(output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data["result_id"] == "eval-004"
            assert data["is_correct"] is True
