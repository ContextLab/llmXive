"""Unit tests for the secondary entropy detector (T005)."""
import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.data.entropy_detector import (
    compute_entropy,
    shannon_entropy,
    tokenize_diff,
)


CLEAN_DIFF = (
    "def add(a, b):\n"
    "    return a + b\n"
    "def add(a, b):\n"
    "    return a + b\n"
    "def add(a, b):\n"
    "    return a + b\n"
)

NOISY_DIFF = (
    "x9f2 zq01 aa7b qwe3 lk98 zz71 mm34 pp56 vv89 nn12 "
    "x9f2 zq01 aa7b qwe3 lk98 zz71 mm34 pp56 vv89 nn12"
)


def test_returns_float_between_0_and_1():
    for text in [CLEAN_DIFF, NOISY_DIFF, "", "single_token", None or ""]:
        score = compute_entropy(text)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


def test_empty_diff_is_zero():
    assert compute_entropy("") == 0.0


def test_single_repeated_token_is_zero():
    assert compute_entropy("a a a a a") == 0.0


def test_noisy_diff_higher_entropy_than_clean_diff():
    clean_score = compute_entropy(CLEAN_DIFF)
    noisy_score = compute_entropy(NOISY_DIFF)
    assert noisy_score > clean_score


def test_uniform_distribution_is_one():
    # All tokens equally frequent -> normalised entropy exactly 1.0
    text = "a b c d e f g h"
    assert compute_entropy(text) == 1.0


def test_tokenize_whitespace_split():
    assert tokenize_diff("a  b\nc\td") == ["a", "b", "c", "d"]
    assert tokenize_diff("") == []


def test_shannon_entropy_bits():
    # Two equally likely tokens -> 1 bit of entropy
    assert abs(shannon_entropy(["x", "y"]) - 1.0) < 1e-12
    assert shannon_entropy([]) == 0.0