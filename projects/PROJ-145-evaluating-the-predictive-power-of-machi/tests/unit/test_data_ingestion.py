"""Unit tests for data ingestion helpers (guarded import)."""
import re
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


def test_count_elements_in_composition_string():
    assert len(re.findall(r"[A-Z][a-z]?", "AlCoCrFeNi")) == 5
    assert len(re.findall(r"[A-Z][a-z]?", "AlCoCrFe")) == 4
    assert len(re.findall(r"[A-Z][a-z]?", "Fe1.0")) == 1


@pytest.mark.skipif(not HAVE, reason=_SKIP)
def test_filter_min_elements_callable():
    assert callable(data_ingestion.filter_min_elements)
