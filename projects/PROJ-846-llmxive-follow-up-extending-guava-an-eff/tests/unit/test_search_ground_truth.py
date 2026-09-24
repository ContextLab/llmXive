"""
Unit tests for search_ground_truth.py (T013b)
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.search_ground_truth import scan_file_for_keys, find_ground_truth_annotations, verify_ground_truth
from code.utils.exceptions import GroundTruthSchemaMissingError

class TestScanFileForKeys:
    def test_json_with_annotations(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"annotations": [], "other": "data"}
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        assert scan_file_for_keys(file_path, ["annotations"]) is True
        assert scan_file_for_keys(file_path, ["bboxes"]) is False
        assert scan_file_for_keys(file_path, ["annotations", "bboxes"]) is True

    def test_json_with_bboxes(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"bboxes": [[1, 2, 3, 4]]}
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        assert scan_file_for_keys(file_path, ["bboxes"]) is True

    def test_json_with_objects(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"objects": [{"id": 1}]}
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        assert scan_file_for_keys(file_path, ["objects"]) is True

    def test_json_without_keys(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = {"metadata": {"version": 1}}
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        assert scan_file_for_keys(file_path, ["annotations", "bboxes", "objects"]) is False

    def test_invalid_json(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")
        
        assert scan_file_for_keys(file_path, ["annotations"]) is False

    def test_list_of_dicts(self, tmp_path):
        file_path = tmp_path / "test.json"
        data = [{"annotations": []}, {"id": 1}]
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        assert scan_file_for_keys(file_path, ["annotations"]) is True

class TestFindGroundTruthAnnotations:
    def test_find_in_directory(self, tmp_path):
        # Create structure
        raw_dir = tmp_path / "raw"
        raw_dir.mkdir()
        
        # Valid files
        (raw_dir / "valid1.json").write_text('{"annotations": []}')
        (raw_dir / "valid2.json").write_text('{"bboxes": []}')
        (raw_dir / "valid3.csv").write_text("id,annotations\n1,[]") # CSV header check
        
        # Invalid file
        (raw_dir / "invalid.json").write_text('{"metadata": {}}')
        
        # Nested valid file
        nested = raw_dir / "sub"
        nested.mkdir()
        (nested / "nested.json").write_text('{"objects": []}')
        
        candidates = find_ground_truth_annotations(raw_dir)
        
        assert len(candidates) == 4
        assert all(c.suffix in ['.json', '.csv'] for c in candidates)
        assert not any(c.name == "invalid.json" for c in candidates)

    def test_empty_directory(self, tmp_path):
        raw_dir = tmp_path / "empty_raw"
        raw_dir.mkdir()
        
        candidates = find_ground_truth_annotations(raw_dir)
        assert len(candidates) == 0

    def test_non_existent_directory(self, tmp_path):
        non_existent = tmp_path / "does_not_exist"
        candidates = find_ground_truth_annotations(non_existent)
        assert len(candidates) == 0

class TestVerifyGroundTruth:
    def test_verify_valid_candidates(self, tmp_path):
        candidates = [tmp_path / "a.json", tmp_path / "b.json"]
        valid = verify_ground_truth(candidates)
        assert valid == candidates

    def test_verify_empty_candidates(self, tmp_path):
        with pytest.raises(GroundTruthSchemaMissingError):
            verify_ground_truth([])
        
        with pytest.raises(GroundTruthSchemaMissingError):
            verify_ground_truth(None)