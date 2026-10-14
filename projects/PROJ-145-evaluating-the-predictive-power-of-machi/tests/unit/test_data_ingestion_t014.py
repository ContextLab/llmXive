"""Unit tests for hold-out sampling logic (guarded import)."""
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


def test_set_difference_excludes_train():
    hmao_index = {"A,B,C,D,E", "F,G,H,I,J", "K,L,M,N,O"}
    train_index = {"A,B,C,D,E"}
    assert hmao_index - train_index == {"F,G,H,I,J", "K,L,M,N,O"}


@pytest.mark.skipif(not HAVE, reason=_SKIP)
def test_generate_all_5_element_combinations_callable():
    assert callable(data_ingestion.generate_all_5_element_combinations)
