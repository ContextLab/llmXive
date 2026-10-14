"""Integration test for the dedup index (guarded import)."""
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


def test_project_root_importable():
    import code  # noqa: F401

    assert Path(code.__file__).parent == PROJECT_ROOT / "code"


@pytest.mark.skipif(not HAVE, reason=_SKIP)
def test_dedup_index_api_surface():
    for name in (
        "build_deduplicated_composition_index",
        "load_hmao_index_for_novelty_check",
    ):
        assert callable(getattr(data_ingestion, name)), name