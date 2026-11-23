import json
import tempfile
import os
from pathlib import Path
import pytest

from src.feature_extraction.exporter import (
    export_features_to_jsonl,
    generate_feature_manifest,
    validate_feature_record,
    FEATURE_RECORD_SCHEMA
)
from src.utils.validation import ValidationError

@pytest.fixture
def sample_feature_record():
    return {
        "frame_id": 1,
        "timestamp_ms": 33,
        "chunk_id": "chunk_001",
        "video_id": "vid_001",
        "features": {
            "layer_0": [0.1, 0.2, 0.3],
            "attention": [0.9]
        },
        "feature_vector_dimension": 4,
        "labels": {"ground_truth": "fall"}
    }

@pytest.fixture
def invalid_record_missing_field():
    return {
        "frame_id": 1,
        # Missing timestamp_ms
        "chunk_id": "chunk_001",
        "video_id": "vid_001",
        "features": {"layer_0": [0.1]},
        "feature_vector_dimension": 1
    }

@pytest.fixture
def invalid_record_empty_features():
    return {
        "frame_id": 1,
        "timestamp_ms": 33,
        "chunk_id": "chunk_001",
        "video_id": "vid_001",
        "features": {},
        "feature_vector_dimension": 0
    }

class TestFeatureExporter:
    def test_export_creates_file(self, sample_feature_record, tmp_path):
        output_file = tmp_path / "test.jsonl"
        count = export_features_to_jsonl([sample_feature_record], output_file)
        
        assert count == 1
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            line = f.readline()
            data = json.loads(line)
            assert data["frame_id"] == 1
            assert "layer_0" in data["features"]

    def test_export_multiple_records(self, sample_feature_record, tmp_path):
        records = [sample_feature_record for _ in range(5)]
        output_file = tmp_path / "test_multi.jsonl"
        count = export_features_to_jsonl(records, output_file)
        
        assert count == 5
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 5

    def test_export_validates_schema(self, invalid_record_missing_field, tmp_path):
        output_file = tmp_path / "test_invalid.jsonl"
        with pytest.raises(ValidationError):
            export_features_to_jsonl([invalid_record_missing_field], output_file)

    def test_export_validates_empty_features(self, invalid_record_empty_features, tmp_path):
        output_file = tmp_path / "test_empty.jsonl"
        with pytest.raises(ValidationError):
            export_features_to_jsonl([invalid_record_empty_features], output_file)

    def test_generate_manifest(self, sample_feature_record, tmp_path):
        # First export a file
        output_file = tmp_path / "features.jsonl"
        export_features_to_jsonl([sample_feature_record] * 10, output_file)
        
        manifest_path = tmp_path / "manifest.json"
        manifest = generate_feature_manifest(tmp_path, manifest_path)
        
        assert manifest["total_records"] == 10
        assert len(manifest["files"]) == 1
        assert manifest["files"][0]["record_count"] == 10
        assert "features.jsonl" in manifest["files"][0]["path"]

    def test_validate_feature_record_success(self, sample_feature_record):
        assert validate_feature_record(sample_feature_record) is True

    def test_validate_feature_record_failure(self, invalid_record_missing_field):
        with pytest.raises(ValidationError):
            validate_feature_record(invalid_record_missing_field)
