"""Tests for the Monte-Carlo power analysis (T002)."""

from __future__ import annotations

import re

from llmxive_toolkit import paths

from code.power_analysis import (
    N_SAMPLES,
    estimate_power,
    format_report,
    run_power_analysis,
)


def _parse_report(text: str) -> tuple[float, bool]:
    power_match = re.search(
        rf"estimated_power_n{N_SAMPLES}:\s*([0-9.]+)", text
    )
    assert power_match is not None, "missing numeric power estimate"
    power = float(power_match.group(1))
    flag_match = re.search(r"exploratory:\s*(true|false)", text)
    assert flag_match is not None, "missing exploratory flag"
    exploratory = flag_match.group(1) == "true"
    return power, exploratory


def test_power_report_exists_and_is_consistent():
    result = run_power_analysis(n_replicates=200)
    report_path = paths.results("power_report.md")
    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    power, exploratory = _parse_report(text)
    assert 0.0 <= power <= 1.0
    assert exploratory == (power < 0.8)
    assert result["exploratory"] == exploratory


def test_format_report_low_power_branch_sets_exploratory_true():
    text = format_report(0.42)
    power, exploratory = _parse_report(text)
    assert power == 0.42
    assert exploratory is True


def test_format_report_high_power_branch_sets_exploratory_false():
    text = format_report(0.95)
    power, exploratory = _parse_report(text)
    assert power == 0.95
    assert exploratory is False


def test_estimate_power_is_deterministic_with_pinned_seed():
    a = estimate_power(n_replicates=50)
    b = estimate_power(n_replicates=50)
    assert a == b
    assert 0.0 <= a <= 1.0


def test_power_uses_pinned_seed_from_seeds_module():
    import numpy as np

    from code.seeds import SEED

    rng = np.random.default_rng(SEED)
    assert SEED == 42
    assert rng is not None
    # The estimate must be reproducible from the pinned seed alone.
    assert estimate_power(n_replicates=30, seed=SEED) == estimate_power(
        n_replicates=30, seed=SEED
    )
