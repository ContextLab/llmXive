"""
Integration test for synthetic uniform and biased residue datasets.

This test generates synthetic datasets for each supported prime,
runs the full statistical pipeline (chi‑squared test and flag
generation), and asserts that the generated flags correctly reflect
the expected pass/fail outcome:

* Uniform synthetic data → ``alpha_pass`` should be ``True``.
* Biased synthetic data → ``alpha_pass`` should be ``False``.
"""

import json
import sys
import os
from pathlib import Path

# Ensure the project's ``code`` directory is on the import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))

# Imports from the project.
from synthetic_validation import (
    generate_uniform_counts,
    generate_biased_counts,
    run_stats_and_flag,
)
from llmxive_toolkit import paths

import pytest

@pytest.mark.parametrize("prime", [3, 5, 7, 11])
def test_synthetic_uniform_and_biased(prime, tmp_path):
    """
    For each supported prime:
    1. Create a uniform synthetic residue count map.
    2. Run the statistical analysis and flag generation.
    3. Verify that ``alpha_pass`` is ``True``.
    4. Create a biased synthetic residue count map.
    5. Run the pipeline again.
    6. Verify that ``alpha_pass`` is ``False``.
    """

    # Use a modest N that keeps the test fast while still
    # satisfying the χ² expected‑count ≥ 5 condition for the
    # uniform case.
    N = 120  # 120 is divisible by all supported primes.

    # -----------------------------------------------------------------
    # Uniform synthetic dataset
    # -----------------------------------------------------------------
    uniform_counts = generate_uniform_counts(N, prime)

    # Run the full pipeline; the function writes both the
    # statistical result JSON and the flag JSON.
    uniform_flags = run_stats_and_flag(
        observed_counts=uniform_counts,
        prime=prime,
        N=N,
        output_dir=str(tmp_path),
    )

    # The flag file is written to the standard ``results/reports``
    # location by ``flags.generate_flag_from_result``.
    uniform_flag_path = paths.results(f"flag_{prime}_{N}.json")
    assert uniform_flag_path.is_file(), f"Flag file missing: {uniform_flag_path}"
    with open(uniform_flag_path, "r", encoding="utf-8") as f:
        uniform_flag_content = json.load(f)

    # The function returns the same dictionary that is written to
    # disk; we assert consistency.
    assert uniform_flags == uniform_flag_content
    assert uniform_flag_content["alpha_pass"] is True, (
        f"Uniform synthetic data for prime {prime} should pass "
        f"the α=0.05 test."
    )

    # -----------------------------------------------------------------
    # Biased synthetic dataset
    # -----------------------------------------------------------------
    biased_counts = generate_biased_counts(
        N=N,
        prime=prime,
        bias_residue=0,   # inflate the zero‑class
        bias_factor=1.5, # 50 % increase over uniform expectation
    )

    biased_flags = run_stats_and_flag(
        observed_counts=biased_counts,
        prime=prime,
        N=N,
        output_dir=str(tmp_path),
    )

    biased_flag_path = paths.results(f"flag_{prime}_{N}.json")
    assert biased_flag_path.is_file(), f"Flag file missing: {biased_flag_path}"
    with open(biased_flag_path, "r", encoding="utf-8") as f:
        biased_flag_content = json.load(f)

    assert biased_flags == biased_flag_content
    assert biased_flag_content["alpha_pass"] is False, (
        f"Biased synthetic data for prime {prime} should fail "
        f"the α=0.05 test."
    )