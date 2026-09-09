"""
Integration test for end-to-end trajectory generation (User Story 1).

This test verifies the complete pipeline of synthetic benchmark generation:
1. Execution of the generator script (synthetic_benchmark.py)
2. Validation of output file existence and format (JSONL)
3. Verification of trajectory count (>= 50 per Spec FR-001)
4. Validation of dependency link injection (via validator module)
5. Validation of coherence (via coherence_validator module)

NOTE: This test is expected to fail initially until T011 (implementation) is complete.
It is parallel-safe and follows TDD principles.
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest

# Import validation utilities from the project
from data_generation.validator import load_trajectories, validate_dependency_links
from data_generation.coherence_validator import validate_benchmark_coherence
from utils.config import get_project_root, get_data_dir


class TestBenchmarkGenerationE2E:
    """Integration tests for the full benchmark generation pipeline."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Ensure clean state before and after test."""
        self.project_root = get_project_root()
        self.data_dir = get_data_dir()
        self.output_file = self.data_dir / "synthetic_benchmark" / "trajectories.jsonl"
        
        # Clean up any existing output file before the test
        if self.output_file.exists():
            self.output_file.unlink()

        yield

        # Optional: Clean up after test if desired, or leave for inspection
        # if self.output_file.exists():
        #     self.output_file.unlink()

    def test_generator_script_execution(self):
        """
        Test that the synthetic_benchmark.py script runs successfully and produces output.
        
        This test executes the generator script as a subprocess and verifies:
        1. The script exits with code 0
        2. The output file is created
        3. The output file is not empty
        """
        generator_script = self.project_root / "code" / "data_generation" / "synthetic_benchmark.py"
        
        if not generator_script.exists():
            pytest.skip(f"Generator script not found at {generator_script}. "
                        "This is expected if T011 (implementation) is not yet complete.")

        # Run the generator script
        result = subprocess.run(
            [sys.executable, str(generator_script)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        # Assert script execution was successful
        assert result.returncode == 0, (
            f"Generator script failed with exit code {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Assert output file exists
        assert self.output_file.exists(), (
            f"Output file {self.output_file} was not created after running the generator."
        )

        # Assert output file is not empty
        assert self.output_file.stat().st_size > 0, (
            f"Output file {self.output_file} is empty."
        )

    def test_output_format_and_count(self):
        """
        Test that the output file is valid JSONL and contains >= 50 trajectories.
        
        This verifies Spec FR-001 requirement for >= 50 trajectories.
        """
        # Skip if file doesn't exist (generator not run yet)
        if not self.output_file.exists():
            pytest.skip(f"Output file {self.output_file} does not exist. "
                        "Run the generator script first.")

        # Load and validate trajectories
        trajectories = load_trajectories(str(self.output_file))
        
        assert isinstance(trajectories, list), "Trajectories should be a list."
        assert len(trajectories) > 0, "Trajectories list should not be empty."
        
        # Verify count meets Spec FR-001 requirement
        assert len(trajectories) >= 50, (
            f"Trajectory count ({len(trajectories)}) is less than required 50. "
            "Spec FR-001 mandates >= 50 trajectories."
        )

        # Verify each trajectory has required structure
        for i, traj in enumerate(trajectories):
            assert isinstance(traj, dict), f"Trajectory {i} should be a dictionary."
            assert "trajectory_id" in traj, f"Trajectory {i} missing 'trajectory_id'."
            assert "steps" in traj, f"Trajectory {i} missing 'steps'."
            assert isinstance(traj["steps"], list), f"Trajectory {i} 'steps' should be a list."

    def test_dependency_links_validation(self):
        """
        Test that dependency links are correctly injected and valid.
        
        This verifies that the generator properly creates cross-app dependencies
        as required by the user story.
        """
        if not self.output_file.exists():
            pytest.skip(f"Output file {self.output_file} does not exist.")

        trajectories = load_trajectories(str(self.output_file))
        
        # Validate dependency links
        is_valid, issues = validate_dependency_links(trajectories)
        
        # Assert that the benchmark passes dependency validation
        assert is_valid, (
            f"Dependency link validation failed with {len(issues)} issues.\n"
            f"First 5 issues: {issues[:5]}"
        )

    def test_coherence_validation(self):
        """
        Test that the generated benchmark passes coherence checks.
        
        This verifies semantic plausibility and temporal coherence of trajectories.
        """
        if not self.output_file.exists():
            pytest.skip(f"Output file {self.output_file} does not exist.")

        # Validate benchmark coherence
        is_valid, issues = validate_benchmark_coherence(str(self.output_file))
        
        # Assert coherence validation passes
        assert is_valid, (
            f"Coherence validation failed with {len(issues)} issues.\n"
            f"First 5 issues: {issues[:5]}"
        )

    def test_end_to_end_pipeline(self):
        """
        Full end-to-end test: Run generator -> Validate output -> Check all criteria.
        
        This combines all previous tests into a single integration test that
        validates the complete pipeline.
        """
        # Step 1: Run generator
        generator_script = self.project_root / "code" / "data_generation" / "synthetic_benchmark.py"
        
        if not generator_script.exists():
            pytest.skip(f"Generator script not found at {generator_script}. "
                        "This is expected if T011 (implementation) is not yet complete.")

        result = subprocess.run(
            [sys.executable, str(generator_script)],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"Generator script failed.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

        # Step 2: Validate output
        if not self.output_file.exists():
            pytest.fail("Generator did not create output file.")

        trajectories = load_trajectories(str(self.output_file))

        # Step 3: Verify count
        assert len(trajectories) >= 50, f"Insufficient trajectories: {len(trajectories)} < 50"

        # Step 4: Verify dependencies
        is_valid, _ = validate_dependency_links(trajectories)
        assert is_valid, "Dependency links validation failed."

        # Step 5: Verify coherence
        is_valid, _ = validate_benchmark_coherence(str(self.output_file))
        assert is_valid, "Coherence validation failed."

        # All checks passed
        assert True, "End-to-end benchmark generation pipeline validated successfully."