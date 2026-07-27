"""
Unit tests for the validators module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from src.utils.validators import (
    TokenSequence,
    ValidityLabel,
    LayerEntropy,
    EntropyProfile,
    validate_token_sequence,
    validate_validity_label,
    validate_entropy_profile,
    validate_merged_record,
    validate_json_schema,
    load_and_validate_jsonl
)


class TestTokenSequenceValidation:
    """Tests for TokenSequence validation."""

    def test_valid_token_sequence(self):
        """Test that a valid TokenSequence passes validation."""
        seq = TokenSequence(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="gsm8k",
            tokens=["Hello", "world", "!"],
            token_ids=[101, 102, 103],
            generation_time_ms=150.5,
            model_name="test-model",
            temperature=0.7,
            seed=42
        )
        is_valid, errors = validate_token_sequence(seq)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_task_type(self):
        """Test that invalid task_type is caught."""
        seq = TokenSequence(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="invalid_type",
            tokens=["Hello"]
        )
        is_valid, errors = validate_token_sequence(seq)
        assert not is_valid
        assert any("task_type" in err for err in errors)

    def test_mismatched_token_ids(self):
        """Test that mismatched token_ids length is caught."""
        seq = TokenSequence(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="gsm8k",
            tokens=["Hello", "world"],
            token_ids=[101]  # Length mismatch
        )
        is_valid, errors = validate_token_sequence(seq)
        assert not is_valid
        assert any("length" in err.lower() for err in errors)

    def test_negative_generation_time(self):
        """Test that negative generation_time_ms is caught."""
        seq = TokenSequence(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="gsm8k",
            tokens=["Hello"],
            generation_time_ms=-10.0
        )
        is_valid, errors = validate_token_sequence(seq)
        assert not is_valid
        assert any("non-negative" in err for err in errors)

    def test_temperature_out_of_range(self):
        """Test that temperature out of range is caught."""
        seq = TokenSequence(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="gsm8k",
            tokens=["Hello"],
            temperature=2.5
        )
        is_valid, errors = validate_token_sequence(seq)
        assert not is_valid
        assert any("temperature" in err for err in errors)


class TestValidityLabelValidation:
    """Tests for ValidityLabel validation."""

    def test_valid_validity_label(self):
        """Test that a valid ValidityLabel passes validation."""
        label = ValidityLabel(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            labels=[True, False, True],
            validity_scores=[0.9, 0.3, 0.8],
            matching_path_id="path_001"
        )
        is_valid, errors = validate_validity_label(label)
        assert is_valid
        assert len(errors) == 0

    def test_empty_labels(self):
        """Test that empty labels list is caught."""
        label = ValidityLabel(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            labels=[]
        )
        is_valid, errors = validate_validity_label(label)
        assert not is_valid
        assert any("non-empty" in err for err in errors)

    def test_non_boolean_labels(self):
        """Test that non-boolean labels are caught."""
        label = ValidityLabel(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            labels=[True, "invalid", False]
        )
        is_valid, errors = validate_validity_label(label)
        assert not is_valid
        assert any("boolean" in err for err in errors)

    def test_mismatched_scores_length(self):
        """Test that mismatched validity_scores length is caught."""
        label = ValidityLabel(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            labels=[True, False],
            validity_scores=[0.9]  # Length mismatch
        )
        is_valid, errors = validate_validity_label(label)
        assert not is_valid
        assert any("length" in err.lower() for err in errors)


class TestEntropyProfileValidation:
    """Tests for EntropyProfile validation."""

    def test_valid_entropy_profile(self):
        """Test that a valid EntropyProfile passes validation."""
        layer_entropies = [
            LayerEntropy(layer_index=0, entropy_value=1.2, layer_name="layer_0"),
            LayerEntropy(layer_index=1, entropy_value=0.8, layer_name="layer_1"),
            LayerEntropy(layer_index=2, entropy_value=1.5, layer_name="layer_2")
        ]
        profile = EntropyProfile(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="gsm8k",
            token_index=0,
            token_id=101,
            token_text="Hello",
            layer_entropies=layer_entropies,
            mean_entropy=1.167,
            max_entropy=1.5,
            min_entropy=0.8,
            entropy_std=0.29,
            validity_label=True
        )
        is_valid, errors = validate_entropy_profile(profile)
        assert is_valid
        assert len(errors) == 0

    def test_negative_token_index(self):
        """Test that negative token_index is caught."""
        layer_entropies = [LayerEntropy(layer_index=0, entropy_value=1.2)]
        profile = EntropyProfile(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="gsm8k",
            token_index=-1,
            token_id=101,
            token_text="Hello",
            layer_entropies=layer_entropies,
            mean_entropy=1.2,
            max_entropy=1.2,
            min_entropy=1.2,
            entropy_std=0.0
        )
        is_valid, errors = validate_entropy_profile(profile)
        assert not is_valid
        assert any("non-negative" in err for err in errors)

    def test_negative_entropy_value(self):
        """Test that negative entropy_value is caught."""
        layer_entropies = [LayerEntropy(layer_index=0, entropy_value=-0.5)]
        profile = EntropyProfile(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="gsm8k",
            token_index=0,
            token_id=101,
            token_text="Hello",
            layer_entropies=layer_entropies,
            mean_entropy=0.0,
            max_entropy=0.0,
            min_entropy=0.0,
            entropy_std=0.0
        )
        is_valid, errors = validate_entropy_profile(profile)
        assert not is_valid
        assert any("non-negative" in err for err in errors)

    def test_empty_layer_entropies(self):
        """Test that empty layer_entropies is caught."""
        profile = EntropyProfile(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="gsm8k",
            token_index=0,
            token_id=101,
            token_text="Hello",
            layer_entropies=[],
            mean_entropy=0.0,
            max_entropy=0.0,
            min_entropy=0.0,
            entropy_std=0.0
        )
        is_valid, errors = validate_entropy_profile(profile)
        assert not is_valid
        assert any("non-empty" in err for err in errors)

    def test_invalid_task_type(self):
        """Test that invalid task_type in EntropyProfile is caught."""
        layer_entropies = [LayerEntropy(layer_index=0, entropy_value=1.2)]
        profile = EntropyProfile(
            sequence_id="seq_001",
            prompt_id="prompt_001",
            task_type="invalid",
            token_index=0,
            token_id=101,
            token_text="Hello",
            layer_entropies=layer_entropies,
            mean_entropy=1.2,
            max_entropy=1.2,
            min_entropy=1.2,
            entropy_std=0.0
        )
        is_valid, errors = validate_entropy_profile(profile)
        assert not is_valid
        assert any("task_type" in err for err in errors)


class TestMergedRecordValidation:
    """Tests for merged record validation."""

    def test_valid_merged_record(self):
        """Test that a valid merged record passes validation."""
        record = {
            "sequence_id": "seq_001",
            "prompt_id": "prompt_001",
            "task_type": "gsm8k",
            "tokens": ["Hello", "world"],
            "labels": [True, False],
            "entropy_data": {"mean": 1.2}
        }
        is_valid, errors = validate_merged_record(record)
        assert is_valid
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test that missing required field is caught."""
        record = {
            "sequence_id": "seq_001",
            "task_type": "gsm8k",
            "tokens": ["Hello"],
            "labels": [True]
        }
        is_valid, errors = validate_merged_record(record)
        assert not is_valid
        assert any("Missing required field" in err for err in errors)

    def test_labels_tokens_length_mismatch(self):
        """Test that labels/tokens length mismatch is caught."""
        record = {
            "sequence_id": "seq_001",
            "prompt_id": "prompt_001",
            "task_type": "gsm8k",
            "tokens": ["Hello", "world"],
            "labels": [True]  # Length mismatch
        }
        is_valid, errors = validate_merged_record(record)
        assert not is_valid
        assert any("length" in err.lower() for err in errors)


class TestJsonSchemaValidation:
    """Tests for JSON schema validation."""

    def test_valid_schema_compliance(self):
        """Test that data compliant with schema passes."""
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        data = {"name": "Alice", "age": 30}
        is_valid, errors = validate_json_schema(data, schema)
        assert is_valid
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test that missing required field in schema is caught."""
        schema = {
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        data = {"name": "Alice"}
        is_valid, errors = validate_json_schema(data, schema)
        assert not is_valid
        assert any("Missing required field" in err for err in errors)

    def test_wrong_type(self):
        """Test that wrong type in schema is caught."""
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer"}
            }
        }
        data = {"age": "thirty"}
        is_valid, errors = validate_json_schema(data, schema)
        assert not is_valid
        assert any("must be of type integer" in err for err in errors)

    def test_array_item_type_check(self):
        """Test that array item type check works."""
        schema = {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "integer"}
                }
            }
        }
        data = {"numbers": [1, 2, "three"]}
        is_valid, errors = validate_json_schema(data, schema)
        assert not is_valid
        assert any("Item 2" in err for err in errors)


class TestLoadAndValidateJsonl:
    """Tests for load_and_validate_jsonl function."""

    def test_valid_jsonl_file(self):
        """Test loading and validating a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"sequence_id": "seq_001", "prompt_id": "p_001", "task_type": "gsm8k", "tokens": ["a"], "labels": [True]}\n')
            f.write('{"sequence_id": "seq_002", "prompt_id": "p_002", "task_type": "minigrid", "tokens": ["b"], "labels": [False]}\n')
            temp_path = f.name

        try:
            valid, invalid = load_and_validate_jsonl(
                temp_path,
                validate_merged_record
            )
            assert len(valid) == 2
            assert len(invalid) == 0
        finally:
            Path(temp_path).unlink()

    def test_invalid_jsonl_file(self):
        """Test loading a JSONL file with some invalid records."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # Valid record
            f.write('{"sequence_id": "seq_001", "prompt_id": "p_001", "task_type": "gsm8k", "tokens": ["a"], "labels": [True]}\n')
            # Invalid record (missing required field)
            f.write('{"sequence_id": "seq_002", "task_type": "gsm8k", "tokens": ["b"], "labels": [False]}\n')
            temp_path = f.name

        try:
            valid, invalid = load_and_validate_jsonl(
                temp_path,
                validate_merged_record
            )
            assert len(valid) == 1
            assert len(invalid) == 1
            assert "Missing required field" in invalid[0]['errors'][0]
        finally:
            Path(temp_path).unlink()

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_and_validate_jsonl("/nonexistent/path/file.jsonl", validate_merged_record)