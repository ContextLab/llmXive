"""
Unit test for convergent validity computation.

This test verifies that the `compute_convergent_correlation` function from
`code/validation/compute_convergent.py` returns a Pearson correlation
coefficient that meets the project's predefined thresholds
(r ≥ 0.30 and p‑value < 0.05) when provided with synthetic data that
exhibits a clear positive relationship between the agency score and an
external scale score.
"""

import pathlib
import pandas as pd
import pytest

# Import the function under test.  The module path follows the project's
# API surface definition.
from validation.compute_convergent import compute_convergent_correlation


@pytest.fixture
def synthetic_data(tmp_path: pathlib.Path) -> pathlib.Path:
    """
    Create a small CSV file containing synthetic agency scores and external
    scale scores with a known positive correlation.
    """
    df = pd.DataFrame(
        {
            # Agency scores are in the range [0, 1]
            "agency_score": [0.1, 0.3, 0.5, 0.7, 0.9],
            # External scale scores are linearly related (r ≈ 1.0)
            "external_score": [1, 3, 5, 7, 9],
        }
    )
    csv_path = tmp_path / "convergent_test.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


def test_compute_convergent_correlation_meets_thresholds(synthetic_data: pathlib.Path):
    """
    Run the convergent‑validity computation on the synthetic CSV and assert
    that the resulting Pearson r meets the project's minimum threshold.
    The function may return either a tuple ``(r, p)`` or a dict with
    ``'correlation'`` and ``'p_value'`` keys – the test handles both cases.
    """
    result = compute_convergent_correlation(str(synthetic_data))

    # Normalise the result to ``corr`` and ``pval`` variables.
    if isinstance(result, dict):
        corr = result.get("correlation")
        pval = result.get("p_value")
    elif isinstance(result, tuple) and len(result) == 2:
        corr, pval = result
    else:
        # Fallback: assume the function returns the correlation directly.
        corr = result
        pval = None

    # Basic sanity checks.
    assert corr is not None, "Correlation value should not be None"
    assert isinstance(corr, (float, int)), "Correlation should be a numeric type"

    # Project‑specific thresholds.
    assert corr >= 0.30, f"Correlation {corr:.3f} is below the required 0.30"

    # If a p‑value is provided, ensure statistical significance.
    if pval is not None:
        assert isinstance(pval, (float, int)), "p‑value should be numeric"
        assert pval < 0.05, f"p‑value {pval:.3f} is not below 0.05"