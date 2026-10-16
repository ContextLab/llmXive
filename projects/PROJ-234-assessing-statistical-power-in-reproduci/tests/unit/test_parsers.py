"""
Unit tests for the regex parsers.
"""

import pytest

from utils.parsers import extract_sample_size, extract_effect_size


@pytest.mark.parametrize(
    "text,expected",
    [
        ("The study had N=150 participants.", 150),
        ("Sample size N = 42.", 42),
        ("No sample size mentioned.", None),
    ],
)
def test_extract_sample_size(text, expected):
    assert extract_sample_size(text) == expected


def test_extract_cohens_d():
    txt = "We observed a medium effect, Cohen's d = 0.45, which was significant."
    result = extract_effect_size(txt)
    assert result == (0.45, "Cohen's d", None)


def test_extract_f_statistic():
    txt = "An ANOVA yielded F(1, 145) = 4.5 (p < .001)."
    result = extract_effect_size(txt)
    # Expected tuple: (value, metric_type, (df1, df2))
    assert result == (4.5, "F", (1, 145))


def test_extract_none_when_no_match():
    txt = "The paper reports a p‑value but no effect size."
    assert extract_effect_size(txt) is None