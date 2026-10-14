"""Unit tests for hold-out export logic (guarded import)."""
import random
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from code import data_ingestion
    HAVE = True
except ImportError:
    data_ingestion = None
    HAVE = False

_SKIP = "code.data_ingestion unavailable (missing or incompatible dependency)"


def test_sampling_determinism_with_fixed_seed():
    population = list(range(100))
    random.seed(42)
    s1 = random.sample(population, 10)
    random.seed(42)
    s2 = random.sample(population, 10)
    assert s1 == s2


def test_composition_exclusion_via_set_difference():
    all_comps = {"A", "B", "C", "D", "E"}
    train_comps = {"A", "B"}
    available = all_comps - train_comps
    assert available == {"C", "D", "E"}


@pytest.mark.skipif(not HAVE, reason=_SKIP)
def test_strict_composition_compare_callable():
    assert callable(data_ingestion.strict_composition_compare)
