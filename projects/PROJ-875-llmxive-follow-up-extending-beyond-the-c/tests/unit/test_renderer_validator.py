import pytest
import os
import json
import tempfile
from utils.renderer_validator import (
    calculate_levenshtein_distance,
    validate_ascii_consistency,
    cross_validate_ascii_json,
    validate_files,
    generate_validation_report
)

class TestLevenshteinDistance:
    def test_identical_strings(self):
        assert calculate_levenshtein_distance("hello", "hello") == 0

    def test_empty_strings(self):
        assert calculate_levenshtein_distance("", "") == 0
        assert calculate_levenshtein_distance("abc", "") == 3
        assert calculate_levenshtein_distance("", "abc") == 3

    def test_simple_difference(self):
        assert calculate_levenshtein_distance("kitten", "sitting") == 3

class TestAsciiConsistency:
    def test_valid_grid(self):
        grid = [
            "#####",
            "#...#",
            "#M..#",
            "#####"
        ]
        is_valid, msg = validate_ascii_consistency('\n'.join(grid))
        assert is_valid
        assert "Valid" in msg

    def test_empty_grid(self):
        is_valid, msg = validate_ascii_consistency("")
        assert not is_valid
        assert "Empty" in msg

    def test_inconsistent_row_lengths(self):
        grid = [
            "#####",
            "#...#",
            "#..#",  # Missing one character
            "#####"
        ]
        is_valid, msg = validate_ascii_consistency('\n'.join(grid))
        assert not is_valid
        assert "Bounds" in msg or "length" in msg

    def test_invalid_characters(self):
        grid = [
            "#####",
            "#...#",
            "#M@.#",  # Invalid character
            "#####"
        ]
        is_valid, msg = validate_ascii_consistency('\n'.join(grid))
        assert not is_valid
        assert "Invalid" in msg or "Coordinates" in msg

class TestCrossValidation:
    def test_matching_grids(self):
        ascii_content = "#####\n#...#\n#M..#\n#####"
        json_data = {
            "grid": [
                ["#", "#", "#", "#", "#"],
                ["#", ".", ".", ".", "#"],
                ["#", "M", ".", ".", "#"],
                ["#", "#", "#", "#", "#"]
            ]
        }
        is_valid, msg = cross_validate_ascii_json(ascii_content, json_data)
        assert is_valid
        assert "Valid" in msg

    def test_mismatched_grids(self):
        ascii_content = "#####\n#...#\n#M..#\n#####"
        json_data = {
            "grid": [
                ["#", "#", "#", "#", "#"],
                ["#", ".", ".", ".", "#"],
                ["#", ".", "M", ".", "#"],  # Player in different position
                ["#", "#", "#", "#", "#"]
            ]
        }
        is_valid, msg = cross_validate_ascii_json(ascii_content, json_data)
        assert not is_valid
        assert "Levenshtein" in msg

    def test_no_grid_in_json(self):
        ascii_content = "#####\n#...#\n#M..#\n#####"
        json_data = {"events": []}
        is_valid, msg = cross_validate_ascii_json(ascii_content, json_data)
        assert is_valid

class TestFileValidation:
    def test_valid_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ascii_path = os.path.join(tmpdir, "test.ascii")
            json_path = os.path.join(tmpdir, "test.json")
            
            with open(ascii_path, 'w') as f:
                f.write("#####\n#...#\n#M..#\n#####")
            
            with open(json_path, 'w') as f:
                json.dump({
                    "grid": [
                        ["#", "#", "#", "#", "#"],
                        ["#", ".", ".", ".", "#"],
                        ["#", "M", ".", ".", "#"],
                        ["#", "#", "#", "#", "#"]
                    ]
                }, f)
            
            result = validate_files(ascii_path, json_path)
            assert result['valid']
            assert len(result['errors']) == 0

    def test_missing_file(self):
        result = validate_files("/nonexistent/file.ascii", "/nonexistent/file.json")
        assert not result['valid']
        assert len(result['errors']) > 0

class TestValidationReport:
    def test_generate_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ascii_dir = os.path.join(tmpdir, "ascii")
            json_dir = os.path.join(tmpdir, "json")
            output_path = os.path.join(tmpdir, "report.json")
            
            os.makedirs(ascii_dir)
            os.makedirs(json_dir)
            
            # Create valid files
            with open(os.path.join(ascii_dir, "test1.ascii"), 'w') as f:
                f.write("#####\n#...#\n#M..#\n#####")
            
            with open(os.path.join(json_dir, "test1.json"), 'w') as f:
                json.dump({
                    "grid": [
                        ["#", "#", "#", "#", "#"],
                        ["#", ".", ".", ".", "#"],
                        ["#", "M", ".", ".", "#"],
                        ["#", "#", "#", "#", "#"]
                    ]
                }, f)
            
            report = generate_validation_report(ascii_dir, json_dir, output_path)
            
            assert report['summary']['total_files'] == 1
            assert report['summary']['valid_files'] == 1
            assert report['summary']['invalid_files'] == 0
            assert report['summary']['overall_valid']
            
            # Verify report file was created
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded_report = json.load(f)
                assert loaded_report == report
