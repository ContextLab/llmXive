"""
Unit tests for code/data/verify_schema.py

These tests verify the semantic validation logic for PubLayNet annotations.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.verify_schema import validate_box, validate_annotation, verify_publaynet_schema


class TestValidateBox:
    """Tests for the validate_box function."""
    
    def test_valid_box(self):
        """Test that a valid box passes validation."""
        box = [100.0, 100.0, 200.0, 200.0]
        is_valid, error_msg = validate_box(box)
        assert is_valid
        assert error_msg == ""
    
    def test_box_too_many_coords(self):
        """Test that a box with too many coordinates fails."""
        box = [100.0, 100.0, 200.0, 200.0, 300.0]
        is_valid, error_msg = validate_box(box)
        assert not is_valid
        assert "4 coordinates" in error_msg
    
    def test_box_too_few_coords(self):
        """Test that a box with too few coordinates fails."""
        box = [100.0, 100.0, 200.0]
        is_valid, error_msg = validate_box(box)
        assert not is_valid
        assert "4 coordinates" in error_msg
    
    def test_negative_coordinates(self):
        """Test that negative coordinates fail validation."""
        box = [-100.0, 100.0, 200.0, 200.0]
        is_valid, error_msg = validate_box(box)
        assert not is_valid
        assert "non-negative" in error_msg
    
    def test_x1_greater_than_x2(self):
        """Test that x1 > x2 fails validation."""
        box = [200.0, 100.0, 100.0, 200.0]
        is_valid, error_msg = validate_box(box)
        assert not is_valid
        assert "x1" in error_msg and "x2" in error_msg
    
    def test_y1_greater_than_y2(self):
        """Test that y1 > y2 fails validation."""
        box = [100.0, 200.0, 200.0, 100.0]
        is_valid, error_msg = validate_box(box)
        assert not is_valid
        assert "y1" in error_msg and "y2" in error_msg
    
    def test_zero_area_box(self):
        """Test that zero-area boxes fail validation."""
        box = [100.0, 100.0, 100.0, 200.0]
        is_valid, error_msg = validate_box(box)
        assert not is_valid
        assert "zero area" in error_msg
    
    def test_box_exceeds_bounds(self):
        """Test that boxes exceeding image bounds fail."""
        box = [100.0, 100.0, 1100.0, 200.0]
        is_valid, error_msg = validate_box(box, image_width=1000, image_height=1000)
        assert not is_valid
        assert "exceeds image bounds" in error_msg


class TestValidateAnnotation:
    """Tests for the validate_annotation function."""
    
    def test_valid_annotation(self):
        """Test that a valid annotation passes."""
        annotation = {
            'boxes': [[100.0, 100.0, 200.0, 200.0], [300.0, 300.0, 400.0, 400.0]],
            'text': ['Title', 'Paragraph']
        }
        errors = validate_annotation(annotation, 0)
        assert len(errors) == 0
    
    def test_missing_boxes_key(self):
        """Test that missing 'boxes' key fails."""
        annotation = {'text': ['Title']}
        errors = validate_annotation(annotation, 0)
        assert len(errors) == 1
        assert "Missing 'boxes' key" in errors[0]
    
    def test_missing_text_key(self):
        """Test that missing 'text' key fails."""
        annotation = {'boxes': [[100.0, 100.0, 200.0, 200.0]]}
        errors = validate_annotation(annotation, 0)
        assert len(errors) == 1
        assert "Missing 'text' key" in errors[0]
    
    def test_mismatched_lengths(self):
        """Test that mismatched box/text lengths fail."""
        annotation = {
            'boxes': [[100.0, 100.0, 200.0, 200.0]],
            'text': ['Title', 'Paragraph']
        }
        errors = validate_annotation(annotation, 0)
        assert len(errors) == 1
        assert "Mismatch between boxes" in errors[0]
    
    def test_empty_annotation(self):
        """Test that empty annotations fail."""
        annotation = {'boxes': [], 'text': []}
        errors = validate_annotation(annotation, 0)
        assert len(errors) == 1
        assert "Empty annotation" in errors[0]
    
    def test_invalid_box_in_list(self):
        """Test that invalid boxes in list are detected."""
        annotation = {
            'boxes': [[100.0, 100.0, 200.0, 200.0], [-100.0, 100.0, 200.0, 200.0]],
            'text': ['Title', 'Paragraph']
        }
        errors = validate_annotation(annotation, 0)
        assert len(errors) == 1
        assert "box 1" in errors[0]
    
    def test_non_string_text(self):
        """Test that non-string text fails."""
        annotation = {
            'boxes': [[100.0, 100.0, 200.0, 200.0]],
            'text': [123]
        }
        errors = validate_annotation(annotation, 0)
        assert len(errors) == 1
        assert "Must be string" in errors[0]


class TestVerifyPublaynetSchema:
    """Tests for the verify_publaynet_schema function."""
    
    def test_verify_jsonl_file(self):
        """Test verification of a JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = os.path.join(tmpdir, 'test.jsonl')
            
            # Create valid annotations
            with open(jsonl_path, 'w') as f:
                f.write(json.dumps({'boxes': [[100, 100, 200, 200]], 'text': ['Title']}) + '\n')
                f.write(json.dumps({'boxes': [[300, 300, 400, 400]], 'text': ['Text']}) + '\n')
            
            results = verify_publaynet_schema(jsonl_path)
            
            assert results['total_samples'] == 2
            assert results['valid_samples'] == 2
            assert results['error_rate'] == 0.0
            assert results['verified']
    
    def test_verify_json_file(self):
        """Test verification of a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, 'test.json')
            
            # Create valid annotations
            annotations = [
                {'boxes': [[100, 100, 200, 200]], 'text': ['Title']},
                {'boxes': [[300, 300, 400, 400]], 'text': ['Text']}
            ]
            
            with open(json_path, 'w') as f:
                json.dump(annotations, f)
            
            results = verify_publaynet_schema(json_path)
            
            assert results['total_samples'] == 2
            assert results['valid_samples'] == 2
            assert results['verified']
    
    def test_verify_with_errors(self):
        """Test verification detects errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, 'test.json')
            
            # Create annotations with errors
            annotations = [
                {'boxes': [[100, 100, 200, 200]], 'text': ['Title']},  # Valid
                {'boxes': [[-100, 100, 200, 200]], 'text': ['Text']},  # Invalid box
                {'boxes': [[300, 300, 400, 400]]}  # Missing text
            ]
            
            with open(json_path, 'w') as f:
                json.dump(annotations, f)
            
            results = verify_publaynet_schema(json_path)
            
            assert results['total_samples'] == 3
            assert results['valid_samples'] == 1
            assert results['error_rate'] == 2/3
            assert len(results['errors']) == 2
            assert not results['verified']
    
    def test_max_samples_limit(self):
        """Test that max_samples limits the number of samples checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            jsonl_path = os.path.join(tmpdir, 'test.jsonl')
            
            # Create 10 valid annotations
            with open(jsonl_path, 'w') as f:
                for i in range(10):
                    f.write(json.dumps({'boxes': [[100, 100, 200, 200]], 'text': [f'Text {i}']}) + '\n')
            
            results = verify_publaynet_schema(jsonl_path, max_samples=3)
            
            assert results['total_samples'] == 3
            assert results['valid_samples'] == 3
    
    def test_no_files_found(self):
        """Test behavior when no annotation files are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = verify_publaynet_schema(tmpdir)
            
            assert results['total_samples'] == 0
            assert not results['verified']
            assert "No annotation files found" in results['summary']