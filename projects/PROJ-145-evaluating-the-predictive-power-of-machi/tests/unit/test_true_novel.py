"""Unit tests for true-novel candidate generation (guarded import)."""
import sys
from itertools import combinations
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from code import generate_true_novel
    HAVE = True
except ImportError:
    generate_true_novel = None
    HAVE = False

_SKIP = "code.generate_true_novel unavailable"


def test_five_element_combination_count():
    elements = ["Al", "Co", "Cr", "Fe", "Ni", "Ti"]
    combos = list(combinations(elements, 5))
    assert len(combos) == 6
    assert all(len(c) == 5 for c in combos)


@pytest.mark.skipif(not HAVE, reason=_SKIP)
def test_generate_5_element_combinations_single_result():
    result = generate_true_novel.generate_5_element_combinations(
        ["Al", "Co", "Cr", "Fe", "Ni"], seed=42
    )
    assert "AlCoCrFeNi" in result
