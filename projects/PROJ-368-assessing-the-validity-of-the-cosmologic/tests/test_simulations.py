"""
Unit tests for User Story 3: Simulation Generation and Statistics.

Specifically targets T028: Unit test for `synalm` generation speed (<30s per sim).
"""
import time
import numpy as np
import healpy as hp
import pytest
import sys
import os

# Add parent directory to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulations import generate_isotropic_sims, generate_single_synalm


class TestSynalmGenerationSpeed:
    """
    Tests for T028: Verify that synalm generation meets the <30s per sim constraint.
    """

    def test_synalm_generation_speed(self):
        """
        T028: Unit test for `synalm` generation speed (<30s per sim).

        Generates a single synthetic alm using the Planck best-fit CL and
        verifies the execution time is under the 30-second threshold.
        """
        # Configuration for the test (Nside=128 to match processed data)
        nside = 128
        l_max = 128
        cl = np.zeros(l_max + 1)

        # Construct a simple toy power spectrum for speed testing
        # (Real spectrum is loaded from T024 in the full pipeline, but a
        # simple power law is sufficient for timing the generator).
        l = np.arange(2, l_max + 1)
        cl[2:] = 1e-10 * (l / 2.0) ** (-1.0)
        cl[0] = 0.0
        cl[1] = 0.0

        # Run the generation and measure time
        start_time = time.time()
        alm = generate_single_synalm(nside, cl, seed=42)
        end_time = time.time()

        elapsed = end_time - start_time
        threshold = 30.0  # seconds

        # Verify the result is not None and has correct length
        assert alm is not None, "synalm generation returned None"
        expected_len = hp.Alm.getsize(l_max)
        assert len(alm) == expected_len, f"Expected {expected_len} alm coefficients, got {len(alm)}"

        # Verify timing constraint
        assert elapsed < threshold, (
            f"synalm generation took {elapsed:.2f}s, exceeding limit of {threshold}s. "
            f"Consider optimizing or checking system load."
        )

        # Log the time for visibility
        print(f"Generated single synalm (Nside={nside}, l_max={l_max}) in {elapsed:.2f}s (Limit: {threshold}s)")

    def test_generate_isotropic_sims_batch_speed(self):
        """
        T028 (Extended): Verify batch generation speed for N=10 simulations.

        Ensures that generating a small batch (N=10) completes in reasonable time
        (approx 10 * 30s = 300s max, but should be much faster on modern hardware).
        """
        nside = 128
        l_max = 128
        cl = np.zeros(l_max + 1)
        l = np.arange(2, l_max + 1)
        cl[2:] = 1e-10 * (l / 2.0) ** (-1.0)
        cl[0] = 0.0
        cl[1] = 0.0

        n_sims = 10
        start_time = time.time()

        # Generate 10 simulations
        # Note: In the full pipeline, this uses generate_isotropic_sims
        # which calls generate_single_synalm internally.
        alms_list = []
        for i in range(n_sims):
            alm = generate_single_synalm(nside, cl, seed=42 + i)
            alms_list.append(alm)

        end_time = time.time()
        elapsed = end_time - start_time
        threshold = 180.0  # 3 minutes for 10 sims (generous buffer)

        assert len(alms_list) == n_sims, f"Expected {n_sims} simulations, got {len(alms_list)}"
        assert elapsed < threshold, (
            f"Batch generation of {n_sims} sims took {elapsed:.2f}s, exceeding limit of {threshold}s."
        )

        print(f"Generated {n_sims} synalm simulations in {elapsed:.2f}s (Limit: {threshold}s)")


if __name__ == "__main__":
    # Allow running directly
    pytest.main([__file__, "-v"])
