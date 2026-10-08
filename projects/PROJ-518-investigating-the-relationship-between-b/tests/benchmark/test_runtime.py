import os
import time
import pytest
import numpy as np
import nibabel as nib
from pathlib import Path

from analysis.statistics import run_permutation_test


class TestRuntimeBenchmark:
    """Benchmark tests for T060: Verify permutation test performance."""

    @pytest.fixture(scope="class")
    def dummy_fmri_path(self, tmp_path_factory):
        """Create a dummy NIfTI file for benchmarking."""
        # Ensure the fixtures directory exists
        fixtures_dir = Path("tests/fixtures")
        fixtures_dir.mkdir(parents=True, exist_ok=True)
        dummy_path = fixtures_dir / "dummy_fmri.nii.gz"

        # Create a small dummy 4D NIfTI file (10x10x10 voxels, 10 timepoints)
        data = np.random.rand(10, 10, 10, 10).astype(np.float32)
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, str(dummy_path))

        return dummy_path

    def test_permutation_runtime_10_subjects(self, dummy_fmri_path):
        """
        Assert that run_permutation_test completes in a reasonable time
        simulating a subset of 10 subjects.
        
        Note: This test mocks the heavy fMRI processing by using pre-generated
        mock data for flexibility and creativity, focusing only on the permutation
        test runtime itself.
        """
        # Simulate 10 subjects' flexibility and creativity scores
        n_subjects = 10
        np.random.seed(42)
        flexibility = np.random.rand(n_subjects) * 0.5 + 0.1
        creativity = flexibility * 0.8 + np.random.rand(n_subjects) * 0.1 + 10.0

        # Run permutation test with a representative number of permutations
        # Using 1000 permutations for the benchmark (reduced from 10000 for CI speed)
        n_permutations = 1000

        start_time = time.time()
        result = run_permutation_test(flexibility, creativity, n_permutations=n_permutations)
        elapsed_time = time.time() - start_time

        # Assert that the test completed successfully
        assert "empirical_p_value" in result
        assert "distribution_of_max_stats" in result

        # Assert runtime is within acceptable limits
        # 1000 permutations on 10 samples should be very fast (< 1 second)
        # The 6-hour limit in the task is for the full pipeline on all subjects,
        # not this unit-level permutation test.
        assert elapsed_time < 10.0, f"Permutation test took too long: {elapsed_time:.2f}s"

    def test_dummy_fmri_file_exists(self, dummy_fmri_path):
        """Verify the dummy NIfTI file exists and is non-empty."""
        assert os.path.exists(dummy_fmri_path)
        assert os.path.getsize(dummy_fmri_path) > 0
