"""
Unit tests for the statistical significance utilities defined in
``code/eval/metrics.py``.
"""

import numpy as np
import pytest
from scipy.stats import wilcoxon

# The module under test lives in the ``code`` package; ensure it is importable.
# The repository layout adds the project root to ``sys.path`` during test
# collection, so we can import ``eval.metrics`` directly.
from eval.metrics import wilcoxon_test


def test_wilcoxon_returns_correct_values():
    """
    Verify that ``wilcoxon_test`` returns the same statistic and p‑value as
    SciPy's native ``wilcoxon`` function for a known pair of accuracy lists.
    """
    accuracies_a = [0.80, 0.85, 0.90, 0.78, 0.82]
    accuracies_b = [0.75, 0.80, 0.88, 0.77, 0.80]

    # Expected values from SciPy
    expected_stat, expected_p = wilcoxon(accuracies_a, accuracies_b)

    result = wilcoxon_test(accuracies_a, accuracies_b)

    assert result["statistic"] == expected_stat
    assert np.isclose(result["p_value"], expected_p)


def test_wilcoxon_raises_on_mismatched_lengths():
    """
    The wrapper should raise a ``ValueError`` when the two input sequences
    do not have the same length.
    """
    a = [0.8, 0.85, 0.9]
    b = [0.75, 0.80]  # shorter

    with pytest.raises(ValueError, match="same length"):
        wilcoxon_test(a, b)