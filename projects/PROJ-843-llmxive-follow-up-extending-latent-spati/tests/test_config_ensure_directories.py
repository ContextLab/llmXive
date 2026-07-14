"""
Basic sanity test for the flexible ``ensure_directories`` helper added to
``code/config.py``. The test creates temporary directories, invokes the helper
with several calling styles and checks that the directories have been created.
"""

import shutil
from pathlib import Path

import pytest

from config import ensure_directories


@pytest.fixture
def tmp_root(tmp_path):
    # Create a fresh temporary root that will be removed after the test.
    return tmp_path


def test_ensure_directories_various_calls(tmp_root):
    # Call with no arguments – should be a no‑op and not raise.
    ensure_directories()

    # Single Path argument.
    a = tmp_root / "a"
    ensure_directories(a)
    assert a.is_dir()

    # Multiple arguments, mixing Path and string.
    b = tmp_root / "b"
    c = tmp_root / "c"
    ensure_directories(b, str(c))
    assert b.is_dir() and c.is_dir()

    # Iterable argument.
    d = tmp_root / "d"
    e = tmp_root / "e"
    ensure_directories([d, e])
    assert d.is_dir() and e.is_dir()

    # Mixed var‑args + iterable.
    f = tmp_root / "f"
    g = tmp_root / "g"
    h = tmp_root / "h"
    ensure_directories(f, [g, h])
    assert f.is_dir() and g.is_dir() and h.is_dir()

    # Clean up (pytest will also clean the tmp_path automatically).
    shutil.rmtree(tmp_root)