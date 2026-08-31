"""
Contract tests for schema validation.

These tests verify that the contract schemas correctly validate
data according to the defined specifications.
"""
import pytest
from pydantic import ValidationError
from contracts import FeatureVector, GroundTruth, Prediction, ModelArtifact
from contracts.ground_truth import SweepResult
from contracts.model_artifact import ModelType

class TestFeatureVector:
    """Tests for FeatureVector schema."""

    def test_valid_feature_vector(self):
        """Test creation of a valid FeatureVector."""
        fv = FeatureVector(
            sample_id="sample_001",
            prompt_length=128,
            mean_attention_entropy=2.5,
            hidden_state_norm=1.2
        )
        assert fv.sample_id == "sample_001"
        assert fv.prompt_length == 128
        assert fv.mean_attention_entropy == 2.5
        assert fv.hidden_state_norm == 1.2

    def test_negative_entropy_rejected(self):
        """Test that NaN/Inf entropy is rejected."""
        import math
        with pytest.raises(ValidationError):
            FeatureVector(
                sample_id="sample_001",
                prompt_length=128,
                mean_attention_entropy=float('nan'),
                hidden_state_norm=1.2
            )

    def test_negative_norm_rejected(self):
        """Test that negative hidden state norm is rejected."""
        with pytest.raises(ValidationError):
            FeatureVector(
                sample_id="sample_001",
                prompt_length=128,
                mean_attention_entropy=2.5,
                hidden_state_norm=-1.0
            )

class TestGroundTruth:
    """Tests for GroundTruth schema."""

    def test_valid_ground_truth(self):
        """Test creation of a valid GroundTruth."""
        gt = GroundTruth(
            sample_id="sample_001",
            block_sizes_tested=[1, 2, 4, 8],
            sweep_results=[
                SweepResult(block_size=1, latency_ms=10.0, success=True),
                SweepResult(block_size=2, latency_ms=8.0, success=True),
                SweepResult(block_size=4, latency_ms=12.0, success=True),
                SweepResult(block_size=8, latency_ms=20.0, success=True, oom_error=None)
            ],
            optimal_block_size=2
        )
        assert gt.sample_id == "sample_001"
        assert gt.optimal_block_size == 2

    def test_optimal_must_be_successful(self):
        """Test that optimal block size must be from a successful result."""
        with pytest.raises(ValidationError):
            GroundTruth(
                sample_id="sample_001",
                block_sizes_tested=[1, 2],
                sweep_results=[
                    SweepResult(block_size=1, latency_ms=10.0, success=False, oom_error="OOM"),
                    SweepResult(block_size=2, latency_ms=8.0, success=True)
                ],
                optimal_block_size=1  # Should fail: 1 was not successful
            )

    def test_no_successful_results(self):
        """Test that no successful results raises error."""
        with pytest.raises(ValidationError):
            GroundTruth(
                sample_id="sample_001",
                block_sizes_tested=[1, 2],
                sweep_results=[
                    SweepResult(block_size=1, latency_ms=10.0, success=False, oom_error="OOM"),
                    SweepResult(block_size=2, latency_ms=8.0, success=False, oom_error="OOM")
                ],
                optimal_block_size=1
            )

class TestPrediction:
    """Tests for Prediction schema."""

    def test_valid_prediction(self):
        """Test creation of a valid Prediction."""
        pred = Prediction(
            sample_id="sample_001",
            model_id="xgb_model_v1",
            predicted_block_size=4,
            prediction_confidence=0.85
        )
        assert pred.sample_id == "sample_001"
        assert pred.predicted_block_size == 4
        assert pred.prediction_confidence == 0.85

    def test_invalid_block_size(self):
        """Test that block size < 1 is rejected."""
        with pytest.raises(ValidationError):
            Prediction(
                sample_id="sample_001",
                model_id="xgb_model_v1",
                predicted_block_size=0
            )

    def test_confidence_bounds(self):
        """Test that confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            Prediction(
                sample_id="sample_001",
                model_id="xgb_model_v1",
                predicted_block_size=4,
                prediction_confidence=1.5
            )

class TestModelArtifact:
    """Tests for ModelArtifact schema."""

    def test_valid_model_artifact(self):
        """Test creation of a valid ModelArtifact."""
        artifact = ModelArtifact(
            model_id="xgb_gsm8k_v1",
            model_type=ModelType.XGBOOST,
            model_path="data/models/xgb_gsm8k_v1.pkl",
            training_dataset="data/processed/training_set.jsonl",
            feature_columns=["prompt_length", "mean_attention_entropy", "hidden_state_norm"],
            target_column="optimal_block_size",
            training_metrics={"mae": 1.2, "rmse": 1.5},
            hyperparameters={"max_depth": 5, "n_estimators": 100}
        )
        assert artifact.model_id == "xgb_gsm8k_v1"
        assert artifact.model_type == ModelType.XGBOOST

    def test_empty_features_rejected(self):
        """Test that empty feature columns are rejected."""
        with pytest.raises(ValidationError):
            ModelArtifact(
                model_id="xgb_gsm8k_v1",
                model_type=ModelType.XGBOOST,
                model_path="data/models/xgb_gsm8k_v1.pkl",
                training_dataset="data/processed/training_set.jsonl",
                feature_columns=[],
                target_column="optimal_block_size"
            )

    def test_empty_target_rejected(self):
        """Test that empty target column is rejected."""
        with pytest.raises(ValidationError):
            ModelArtifact(
                model_id="xgb_gsm8k_v1",
                model_type=ModelType.XGBOOST,
                model_path="data/models/xgb_gsm8k_v1.pkl",
                training_dataset="data/processed/training_set.jsonl",
                feature_columns=["prompt_length"],
                target_column=""
            )