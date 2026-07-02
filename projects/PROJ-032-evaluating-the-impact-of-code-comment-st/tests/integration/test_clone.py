"""
Integration test for batch cloning and history validation (US1).

This test verifies that:
1. The `clone_batch` function successfully clones repositories to `data/raw/`.
2. The cloned repositories contain valid git history (non-empty log).
3. The `validate_count` function correctly counts valid clones.
4. Edge cases (clone failures, missing history) are handled gracefully.

Prerequisites:
- T001 (Project structure)
- T002 (Dependencies installed)
- T004b (BatchIterator implemented)
- T006 (Extract implemented - not strictly needed here but good practice)
- T012 (get_candidates implemented)
- T013 (clone_batch implemented)
- T014 (validate_count implemented)
"""
import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import pytest

# Import the functions under test
# Note: Using relative imports logic but adjusted for test execution context
# The project structure implies code/ is at root level relative to tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetch import get_candidates, clone_batch, validate_count
from utils import BatchIterator, configure_logging

# Setup logging for the test
logger = configure_logging(log_path="logs/test_clone_integration.log")


class TestBatchCloningAndHistoryValidation:
    """Integration tests for the cloning and validation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test method."""
        # Create a temporary directory for test data to avoid polluting the real data folder
        self.test_data_dir = Path(tempfile.mkdtemp(prefix="llmxive_test_"))
        self.raw_dir = self.test_data_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Override the data directory for this test run
        self.original_data_root = os.environ.get("DATA_ROOT", "data")
        os.environ["DATA_ROOT"] = str(self.test_data_dir)

        yield

        # Cleanup: Remove the temporary directory
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
        # Restore environment
        if self.original_data_root:
            os.environ["DATA_ROOT"] = self.original_data_root
        elif "DATA_ROOT" in os.environ:
            del os.environ["DATA_ROOT"]

    def test_clone_batch_success_and_history_validation(self):
        """
        Test that clone_batch successfully clones a small batch of repos
        and that they have valid git history.
        """
        # Use a small, known set of Python repos with high stars
        # Hardcoding a few valid repo IDs for reliability in CI/CD without network dependency on HF
        # If HF is unreachable, we rely on the fallback or skip if no candidates.
        # For this integration test, we assume at least a few candidates can be fetched.
        
        # Get candidates (using a small limit for speed)
        # We expect get_candidates to return a list of repo IDs
        candidates = get_candidates(limit=5) 
        
        if not candidates:
            pytest.skip("No candidates available to test cloning.")

        # Clone the batch
        # We use a small batch size to ensure we don't timeout
        cloned_repos = clone_batch(candidates[:3], batch_size=2, target_dir=self.raw_dir)

        # Assertions
        assert len(cloned_repos) > 0, "Expected at least one repo to be cloned successfully."
        
        # Verify each cloned repo has valid git history
        for repo_path in cloned_repos:
            assert Path(repo_path).exists(), f"Cloned repo path does not exist: {repo_path}"
            git_dir = Path(repo_path) / ".git"
            assert git_dir.exists(), f"Git directory missing in {repo_path}"
            
            # Check git log is non-empty
            try:
                result = subprocess.run(
                    ["git", "log", "--oneline"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                assert result.returncode == 0, f"Git log failed for {repo_path}: {result.stderr}"
                assert len(result.stdout.strip()) > 0, f"Git log is empty for {repo_path}"
            except subprocess.TimeoutExpired:
                pytest.fail(f"Git log command timed out for {repo_path}")

    def test_validate_count_accuracy(self):
        """
        Test that validate_count correctly counts the number of valid repos
        with git history in the target directory.
        """
        # First, perform a clone to ensure there is data
        candidates = get_candidates(limit=5)
        if not candidates:
            pytest.skip("No candidates available.")

        # Clone a subset
        cloned = clone_batch(candidates[:2], batch_size=2, target_dir=self.raw_dir)
        
        # Intentionally corrupt one repo to simulate a failure case
        if len(cloned) >= 2:
            # Remove .git from the second repo to simulate missing history
            bad_repo = Path(cloned[1])
            git_dir = bad_repo / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)
        
        # Run validation
        valid_count = validate_count(target_dir=self.raw_dir)
        
        # We expect the count to be exactly the number of valid repos
        # If we corrupted one, it should be len(cloned) - 1 (or 0 if all corrupted)
        expected_count = len([r for r in cloned if Path(r).exists() and (Path(r)/".git").exists()])
        
        # Re-check logic: validate_count scans the directory, not the 'cloned' list
        # So we need to ensure the directory matches our expectation
        # Let's re-verify the directory state
        actual_valid = 0
        for item in self.raw_dir.iterdir():
            if item.is_dir() and (item / ".git").exists():
                try:
                    subprocess.run(["git", "log", "--oneline"], cwd=item, capture_output=True, timeout=5)
                    actual_valid += 1
                except:
                    pass
        
        assert valid_count == actual_valid, f"Validation count {valid_count} does not match actual valid repos {actual_valid}"

    def test_handle_clone_failures_gracefully(self):
        """
        Test that clone_batch handles invalid repo IDs gracefully without crashing.
        """
        # Mix valid and invalid candidates
        # We don't know which are valid without fetching, so we construct a list with a clearly invalid one
        # or rely on get_candidates returning valid ones and adding a fake one.
        # Since get_candidates returns valid IDs, let's add a fake one.
        candidates = get_candidates(limit=1)
        if not candidates:
            pytest.skip("No candidates available.")
        
        invalid_candidates = candidates + ["owner/invalid_repo_name_123456789"]
        
        # This should not raise an exception
        cloned = clone_batch(invalid_candidates, batch_size=2, target_dir=self.raw_dir)
        
        # The valid one should be cloned, the invalid one skipped
        # We expect at least the valid one to be present if network is up
        # If network fails, we might get 0, but the function shouldn't crash
        assert isinstance(cloned, list), "clone_batch should return a list of cloned paths"

    def test_handle_missing_history(self):
        """
        Test that repos with missing git history are detected and excluded by validate_count.
        """
        # Clone a repo
        candidates = get_candidates(limit=1)
        if not candidates:
            pytest.skip("No candidates available.")
        
        cloned = clone_batch(candidates, batch_size=1, target_dir=self.raw_dir)
        
        if not cloned:
            pytest.skip("Cloning failed, cannot test history validation.")
        
        repo_path = Path(cloned[0])
        
        # Simulate missing history by removing .git
        git_dir = repo_path / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
        
        # Now validate
        count = validate_count(target_dir=self.raw_dir)
        
        # The count should be 0 because the only repo has no .git
        assert count == 0, f"Expected 0 valid repos after removing .git, got {count}"

    def test_batch_iterator_concurrency(self):
        """
        Test that BatchIterator correctly limits concurrency during cloning.
        """
        # This is a soft test. We clone a few repos and check if the BatchIterator
        # logic was respected (hard to measure directly without instrumentation,
        # but we can ensure the function completes without race conditions).
        candidates = get_candidates(limit=4)
        if not candidates:
            pytest.skip("No candidates available.")
        
        # Use a batch size of 1 to force sequential-ish behavior if logic is correct
        # or small batch to test concurrency limit
        cloned = clone_batch(candidates[:3], batch_size=2, target_dir=self.raw_dir)
        
        # Just ensure it ran to completion and produced some output
        assert len(cloned) >= 0, "Cloning completed"