"""
Unit tests for T037: Quantization Level Validator.
"""
import pytest
import logging
from src.services.quantization_level_validator import (
    validate_sample_logits,
    validate_dataset_batch,
    verify_level_coverage,
    MissingQuantizationLevelError
)

@pytest.fixture
def logger():
    return logging.getLogger(__name__)

class TestValidateSampleLogits:
    def test_valid_sample_all_levels(self):
        sample = {
            "input_id": "valid_001",
            "quantized_logits": {
                "INT4": [0.1, 0.2, 0.3],
                "INT8": [0.1, 0.2, 0.3],
                "FP8": [0.1, 0.2, 0.3]
            }
        }
        # Should not raise
        validate_sample_logits(sample)

    def test_missing_level_int4(self):
        sample = {
            "input_id": "missing_int4",
            "quantized_logits": {
                "INT8": [0.1, 0.2],
                "FP8": [0.1, 0.2]
            }
        }
        with pytest.raises(MissingQuantizationLevelError) as exc_info:
            validate_sample_logits(sample)
        
        assert exc_info.value.sample_id == "missing_int4"
        assert "INT4" in exc_info.value.missing_levels

    def test_empty_logits_int8(self):
        sample = {
            "input_id": "empty_int8",
            "quantized_logits": {
                "INT4": [0.1],
                "INT8": [],
                "FP8": [0.1]
            }
        }
        with pytest.raises(MissingQuantizationLevelError) as exc_info:
            validate_sample_logits(sample)
        
        assert "INT8" in exc_info.value.missing_levels

    def test_missing_quantized_logits_key(self):
        sample = {
            "input_id": "no_key",
            "data": "some_data"
        }
        with pytest.raises(MissingQuantizationLevelError) as exc_info:
            validate_sample_logits(sample)
        
        assert exc_info.value.missing_levels == ["INT4", "INT8", "FP8"]

    def test_non_dict_quantized_logits(self):
        sample = {
            "input_id": "bad_type",
            "quantized_logits": "not a dict"
        }
        with pytest.raises(MissingQuantizationLevelError) as exc_info:
            validate_sample_logits(sample)
        
        assert exc_info.value.missing_levels == ["INT4", "INT8", "FP8"]

class TestValidateDatasetBatch:
    def test_batch_all_valid(self, logger):
        batch = [
            {
                "input_id": "v1",
                "quantized_logits": {"INT4": [1], "INT8": [1], "FP8": [1]}
            },
            {
                "input_id": "v2",
                "quantized_logits": {"INT4": [2], "INT8": [2], "FP8": [2]}
            }
        ]
        failed = validate_dataset_batch(batch, logger)
        assert len(failed) == 0

    def test_batch_partial_failures(self, logger):
        batch = [
            {
                "input_id": "v1",
                "quantized_logits": {"INT4": [1], "INT8": [1], "FP8": [1]}
            },
            {
                "input_id": "f1",
                "quantized_logits": {"INT4": [1]} # Missing INT8, FP8
            },
            {
                "input_id": "v2",
                "quantized_logits": {"INT4": [2], "INT8": [2], "FP8": [2]}
            }
        ]
        failed = validate_dataset_batch(batch, logger)
        assert len(failed) == 1
        assert "f1" in failed

class TestVerifyLevelCoverage:
    def test_coverage_complete(self):
        batch = [
            {
                "input_id": "s1",
                "quantized_logits": {"INT4": [1], "INT8": [1], "FP8": [1]}
            }
        ]
        counts = verify_level_coverage(batch)
        assert counts["INT4"] == 1
        assert counts["INT8"] == 1
        assert counts["FP8"] == 1

    def test_coverage_missing_level(self):
        batch = [
            {
                "input_id": "s1",
                "quantized_logits": {"INT4": [1], "INT8": [1]} # Missing FP8
            }
        ]
        with pytest.raises(MissingQuantizationLevelError) as exc_info:
            verify_level_coverage(batch)
        
        assert "FP8" in exc_info.value.missing_levels
        assert exc_info.value.sample_id == "BATCH_TOTAL"

    def test_coverage_empty_batch(self):
        with pytest.raises(MissingQuantizationLevelError) as exc_info:
            verify_level_coverage([])
        
        assert set(exc_info.value.missing_levels) == {"INT4", "INT8", "FP8"}