"""Integration test for the data ingestion pipeline (guarded import)."""
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


def test_processed_data_directory_exists():
    assert (PROJECT_ROOT / "data" / "processed").exists()


@pytest.mark.skipif(not HAVE, reason=_SKIP)
def test_ingestion_api_surface():
    for name in (
        "load_hmao_dataset",
        "filter_min_elements",
        "process_and_save_heas_train",
    ):
        assert callable(getattr(data_ingestion, name)), name
