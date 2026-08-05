import ast
import csv
import tempfile
from pathlib import Path
import pytest

from ast_cloner import IdentifierNormalizer, parse_python_file, compute_clone_density_batch


class TestIdentifierNormalizer:
    def test_normalize_removes_whitespace(self):
        source = "   x = 1   "
        expected = "x = 1"
        assert IdentifierNormalizer.normalize(source) == expected

    def test_normalize_preserves_structure(self):
        source = "def foo():\n    return 1"
        result = IdentifierNormalizer.normalize(source)
        assert "def foo():" in result
        assert "return 1" in result


class TestParsePythonFile:
    def test_valid_python_parses(self):
        source = "x = 1\ny = 2"
        result = parse_python_file(source, "test.py")
        assert isinstance(result, ast.Module)

    def test_invalid_python_raises(self):
        source = "x = "
        with pytest.raises(SyntaxError):
            parse_python_file(source, "test.py")


class TestComputeCloneDensityBatch:
    def test_empty_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Write empty CSV with headers
            with input_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["file_path", "content"])
                writer.writeheader()
            
            result = compute_clone_density_batch(input_path, output_path)
            assert result == 0
            assert output_path.exists()

    def test_unique_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Write CSV with unique files
            with input_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["file_path", "content"])
                writer.writeheader()
                writer.writerow({"file_path": "a.py", "content": "x = 1"})
                writer.writerow({"file_path": "b.py", "content": "y = 2"})
            
            result = compute_clone_density_batch(input_path, output_path)
            assert result == 0
            
            # Verify output
            with output_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert all(not row["is_duplicate"] == "True" for row in rows)

    def test_duplicate_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Write CSV with duplicate files
            with input_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["file_path", "content"])
                writer.writeheader()
                writer.writerow({"file_path": "a.py", "content": "x = 1"})
                writer.writerow({"file_path": "b.py", "content": "x = 1"})  # Duplicate
            
            result = compute_clone_density_batch(input_path, output_path)
            assert result == 0
            
            # Verify output
            with output_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                # One should be marked as duplicate
                duplicates = [row for row in rows if row["is_duplicate"] == "True"]
                assert len(duplicates) == 1

    def test_syntax_error_handling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            # Write CSV with one valid and one invalid file
            with input_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["file_path", "content"])
                writer.writeheader()
                writer.writerow({"file_path": "valid.py", "content": "x = 1"})
                writer.writerow({"file_path": "invalid.py", "content": "x = "})
            
            result = compute_clone_density_batch(input_path, output_path)
            assert result == 0
            
            # Verify output only contains valid file
            with output_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]["file_path"] == "valid.py"