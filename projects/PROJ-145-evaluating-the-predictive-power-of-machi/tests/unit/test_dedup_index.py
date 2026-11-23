"""Unit tests for the deduplicated composition index (guarded import)."""
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


def test_canonical_sorting_is_order_independent():
    a = "-".join(sorted("Fe-Cr-Ni-Mn-Co".split("-")))
    b = "-".join(sorted("Co-Mn-Ni-Cr-Fe".split("-")))
    assert a == b
    assert a != "-".join(sorted("Fe-Cr-Ni-Mn-Cu".split("-")))


@pytest.mark.skipif(not HAVE, reason=_SKIP)
def test_build_deduplicated_composition_index_callable():
    assert callable(data_ingestion.build_deduplicated_composition_index)
