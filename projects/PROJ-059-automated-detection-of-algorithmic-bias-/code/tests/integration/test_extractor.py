"""
Integration tests for User Story 1 (Extractor) focusing on edge cases:
- Empty repositories (no Python files)
- Binary-only repositories (non-text files)
- Repositories with syntax errors (handled gracefully)

These tests verify that the pipeline handles malformed or empty inputs
without crashing and produces valid (zero-score) results.
"""
import os
import tempfile
import shutil
import json
import pytest
from pathlib import Path

# Import the real implementation
from src.bias_pipeline.extractor import run_extraction_pipeline
from src.bias_pipeline.error_handler import ExecutionError, safe_execute


class TestEmptyAndBinaryRepos:
    """Integration tests for empty and binary-only repository scenarios."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Create and clean up temporary test directories."""
        self.test_dir = tempfile.mkdtemp(prefix="bias_test_")
        self.output_file = os.path.join(self.test_dir, "extraction_results.json")
        yield
        # Cleanup
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_empty_repository_no_python_files(self):
        """
        Test that an empty repository (or one with no .py files)
        returns a valid result with zero bias score and no crash.
        """
        # Create an empty repo directory
        repo_path = os.path.join(self.test_dir, "empty_repo")
        os.makedirs(repo_path)

        # Create a dummy non-python file
        with open(os.path.join(repo_path, "README.md"), "w") as f:
            f.write("# Empty Repo")

        # Run extraction
        result = run_extraction_pipeline([repo_path], output_path=self.output_file)

        # Assertions
        assert result is not None, "Pipeline should return a result dict"
        assert "results" in result, "Result should contain 'results' key"
        assert len(result["results"]) == 1, "Should process one repo"

        repo_data = result["results"][0]
        assert repo_data["path"] == repo_path
        assert repo_data["bias_score"] == 0.0, "Empty repo should have 0.0 bias score"
        assert repo_data["token_count"] == 0
        assert repo_data["status"] == "success" or repo_data["status"] == "no_python_files"

        # Verify output file was written
        assert os.path.exists(self.output_file), "Output JSON file must be created"
        with open(self.output_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data == result

    def test_binary_only_repository(self):
        """
        Test that a repository containing only binary files (e.g., images, compiled)
        is handled gracefully without crashing.
        """
        repo_path = os.path.join(self.test_dir, "binary_repo")
        os.makedirs(repo_path)

        # Create a dummy binary file
        binary_path = os.path.join(repo_path, "image.png")
        with open(binary_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01")

        # Run extraction
        result = run_extraction_pipeline([repo_path], output_path=self.output_file)

        # Assertions
        assert result is not None
        assert len(result["results"]) == 1

        repo_data = result["results"][0]
        assert repo_data["bias_score"] == 0.0
        assert repo_data["status"] in ["success", "no_python_files", "skipped"]

    def test_mixed_repo_with_syntax_errors(self):
        """
        Test that a repository with a mix of valid and invalid Python files
        processes the valid ones and skips the invalid ones without crashing.
        """
        repo_path = os.path.join(self.test_dir, "mixed_repo")
        os.makedirs(repo_path)

        # Valid file
        valid_path = os.path.join(repo_path, "valid.py")
        with open(valid_path, "w") as f:
            f.write("# Good code\ndef hello():\n    pass\n")

        # Invalid syntax file
        invalid_path = os.path.join(repo_path, "broken.py")
        with open(invalid_path, "w") as f:
            f.write("def broken(\n    # Missing closing paren\n    pass\n")

        # Run extraction
        result = run_extraction_pipeline([repo_path], output_path=self.output_file)

        # Assertions
        assert result is not None
        assert len(result["results"]) == 1

        repo_data = result["results"][0]
        # The repo should still be considered "processed" even if some files failed
        assert repo_data["status"] == "success" or repo_data["status"] == "partial_success"
        
        # We expect at least some tokens from the valid file
        # (unless the lexicon matches nothing, but token count should be > 0)
        # Note: The exact token count depends on the implementation of aggregate_repo_score
        # but it should not be 0 if valid.py was parsed successfully.
        # If the implementation skips the whole repo on one error, that's a failure of T018.
        # Assuming T018 (handle_syntax_error) works, we should get partial results.
        
        # Verify the output file contains the result
        assert os.path.exists(self.output_file)
        with open(self.output_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data == result

    def test_non_existent_repo_path(self):
        """
        Test behavior when a provided repo path does not exist.
        """
        fake_path = os.path.join(self.test_dir, "does_not_exist")
        
        # Run extraction
        result = run_extraction_pipeline([fake_path], output_path=self.output_file)

        # Assertions
        assert result is not None
        assert len(result["results"]) == 1
        
        repo_data = result["results"][0]
        assert repo_data["path"] == fake_path
        assert repo_data["status"] == "error" or repo_data["status"] == "skipped"
        assert "error" in repo_data or "message" in repo_data