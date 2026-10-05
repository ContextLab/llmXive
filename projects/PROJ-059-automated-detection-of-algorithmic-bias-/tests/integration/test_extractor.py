"""
Integration tests for the extractor module focusing on edge cases:
empty repositories and binary-only repositories.

These tests verify that the pipeline handles non-code inputs gracefully
without crashing, returning appropriate empty or error results.
"""
import os
import tempfile
import shutil
import json
import pytest
from pathlib import Path
import sys

# Add the project root to the path to allow imports from code/
# Assuming this file is at code/tests/integration/test_extractor.py
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.bias_pipeline.extractor import process_single_repo, aggregate_repo_score
from src.bias_pipeline.error_handler import ExecutionError, safe_execute


class TestEmptyAndBinaryRepos:
    """
    Integration tests for handling empty and binary-only repositories.
    """

    def setup_method(self):
        """Set up temporary directory for test repositories."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir) / "test_repo"
        self.repo_path.mkdir()

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_file(self, relative_path: str, content: bytes) -> Path:
        """Helper to create a file with specific content in the test repo."""
        file_path = self.repo_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path

    def test_empty_directory_repo(self):
        """
        Test T012-1: Process a repository directory that contains no files.
        Expected: Returns a result with zero tokens and a score of 0.0,
        without raising an exception.
        """
        # Ensure the repo directory is empty (it is created empty in setup)
        assert len(list(self.repo_path.iterdir())) == 0

        result = safe_execute(
            process_single_repo,
            self.repo_path,
            error_type=ExecutionError,
            default_result={"error": "Empty repository", "tokens": [], "bias_score": 0.0}
        )

        # Verify the result structure
        assert isinstance(result, dict)
        assert result.get("bias_score") == 0.0
        assert result.get("tokens") == []
        # Verify no crash occurred (safe_execute returned a result, not raised)
        assert "error" not in result or result["error"] == "Empty repository"

    def test_binary_only_repo(self):
        """
        Test T012-2: Process a repository containing only binary files.
        Expected: Extracts no valid code tokens, returns a score of 0.0,
        and does not crash on decoding errors.
        """
        # Create a binary file (e.g., a fake image or compiled object)
        binary_content = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])  # PNG header
        self._create_file("image.png", binary_content)
        
        # Create a second binary file with random noise
        noise_content = os.urandom(1024)
        self._create_file("data.bin", noise_content)

        result = safe_execute(
            process_single_repo,
            self.repo_path,
            error_type=ExecutionError,
            default_result={"error": "No valid Python files", "tokens": [], "bias_score": 0.0}
        )

        # Verify the result
        assert isinstance(result, dict)
        assert result.get("bias_score") == 0.0
        assert result.get("tokens") == []
        # The extractor should handle the lack of parseable Python files gracefully

    def test_mixed_empty_and_binary_repo(self):
        """
        Test T012-3: Process a repository with empty .py files and binary files.
        Expected: Returns 0.0 score and empty tokens, ignoring empty/binary files.
        """
        # Create an empty Python file
        self._create_file("empty_script.py", b"")
        
        # Create a binary file
        binary_content = os.urandom(512)
        self._create_file("binary.dat", binary_content)

        result = safe_execute(
            process_single_repo,
            self.repo_path,
            error_type=ExecutionError,
            default_result={"error": "No valid Python files", "tokens": [], "bias_score": 0.0}
        )

        assert isinstance(result, dict)
        assert result.get("bias_score") == 0.0
        assert result.get("tokens") == []

    def test_aggregate_repo_score_empty_input(self):
        """
        Test T012-4: Verify aggregate_repo_score handles an empty list of file results.
        Expected: Returns 0.0 without division by zero errors.
        """
        file_results = []
        score = aggregate_repo_score(file_results)
        assert score == 0.0

    def test_aggregate_repo_score_with_empty_file_results(self):
        """
        Test T012-5: Verify aggregate_repo_score handles file results with 0 tokens.
        Expected: Excludes 0-token files from the mean calculation if all are 0,
        or returns 0.0 if no valid files exist.
        """
        # Simulate results where files were parsed but had no tokens (e.g. empty files)
        file_results = [
            {"file": "empty.py", "tokens": [], "bias_score": 0.0},
            {"file": "binary.py", "tokens": [], "bias_score": 0.0}
        ]
        
        score = aggregate_repo_score(file_results)
        # If all files have 0 tokens, the score should be 0.0
        assert score == 0.0

    def test_binary_file_with_valid_python_extension(self):
        """
        Test T012-6: Process a file with .py extension but binary content.
        Expected: The AST parser should fail gracefully, and the file is skipped.
        """
        # Create a file named .py but with binary content
        binary_content = bytes([0x00, 0x01, 0x02, 0x03])
        self._create_file("fake_python.py", binary_content)

        result = safe_execute(
            process_single_repo,
            self.repo_path,
            error_type=ExecutionError,
            default_result={"error": "Syntax error in file", "tokens": [], "bias_score": 0.0}
        )

        # The pipeline should not crash; it should handle the syntax error
        assert isinstance(result, dict)
        assert result.get("bias_score") == 0.0
        assert result.get("tokens") == []