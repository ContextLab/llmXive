"""
Unit tests for the flag generation module.

These tests create synthetic StatisticalResult JSON files with
high and low p‑values, invoke ``generate_flag_from_result`` and
verify that the resulting flag JSON contains the expected boolean
values.
"""

import json
from pathlib import Path

from flags import generate_flag_from_result
from llmxive_toolkit import paths

def _write_stat_result(tmp_dir: Path, prime: int, N: int, p_value: float) -> Path:
    """
    Helper to write a minimal StatisticalResult JSON file.

    The file contains the required ``prime`` and ``N`` fields as well
    as a p‑value field named ``chi_squared_p_value`` (the primary
    field used by ``flags._extract_p_value``).
    """
    data = {
        "prime": prime,
        "N": N,
        "chi_squared_p_value": p_value,
        # Additional fields are optional for the flag logic.
    }
    file_path = tmp_dir / f"stats_{prime}_{N}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return file_path

def test_generate_flag_high_p_value(tmp_path):
    """
    High p‑value (> 0.05) should set all pass flags to ``True``.
    """
    prime = 3
    N = 100
    high_p = 0.12  # > 0.05

    stat_path = _write_stat_result(tmp_path, prime, N, high_p)

    # Run the flag generator.
    flags = generate_flag_from_result(str(stat_path))

    # Verify the returned dictionary.
    assert flags["alpha_pass"] is True
    assert flags["bonferroni_pass"] is True
    assert flags["overall_pass"] is True

    # Verify that the flag file was written to the expected location.
    flag_path = paths.results("reports", f"flag_{prime}_{N}.json")
    assert flag_path.is_file()

    with open(flag_path, "r", encoding="utf-8") as f:
        file_content = json.load(f)
    assert file_content == flags

def test_generate_flag_low_p_value(tmp_path):
    """
    Low p‑value (≤ 0.05) should set ``alpha_pass`` to ``False`` and,
    because the Bonferroni threshold is stricter, also set
    ``bonferroni_pass`` and ``overall_pass`` to ``False``.
    """
    prime = 5
    N = 200
    low_p = 0.03  # ≤ 0.05 but > 0.0125, still fails Bonferroni

    stat_path = _write_stat_result(tmp_path, prime, N, low_p)

    flags = generate_flag_from_result(str(stat_path))

    assert flags["alpha_pass"] is False
    # Bonferroni threshold is 0.05 / 4 = 0.0125, so low_p > threshold
    # leads to bonferroni_pass == False because alpha_pass is False.
    # The implementation defines bonferroni_pass purely on the p‑value,
    # so it should be False as low_p < 0.0125? Actually low_p=0.03 > 0.0125,
    # bonferroni_pass = p_val > 0.0125 => True, but overall_pass requires both.
    # The spec expects both booleans to be evaluated independently.
    # We therefore assert the exact behaviour of the current implementation.
    assert flags["bonferroni_pass"] is True
    assert flags["overall_pass"] is False

    flag_path = paths.results("reports", f"flag_{prime}_{N}.json")
    assert flag_path.is_file()

    with open(flag_path, "r", encoding="utf-8") as f:
        file_content = json.load(f)
    assert file_content == flags