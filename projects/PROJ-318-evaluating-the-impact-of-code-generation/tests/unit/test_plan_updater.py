import os
import tempfile
from pathlib import Path
import pytest

from code.plan_updater import update_plan_file

def test_update_plan_removes_100_methods():
    """Test that '100 methods' is removed/replaced."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Plan\n\n## Constraints\nMax 100 methods per repo.\n")
        temp_path = f.name

    try:
        update_plan_file(temp_path)
        content = Path(temp_path).read_text()
        assert "100 methods" not in content
        assert "[deferred] methods" in content
    finally:
        os.unlink(temp_path)

def test_update_plan_removes_fallback_note():
    """Test that the 8-bit fallback note is removed."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Plan\n\nNote: If 4-bit fails, fallback to 8-bit.\n")
        temp_path = f.name

    try:
        update_plan_file(temp_path)
        content = Path(temp_path).read_text()
        assert "fallback to 8-bit" not in content
        assert "fallback to full precision" not in content
    finally:
        os.unlink(temp_path)

def test_update_plan_adds_hard_cap():
    """Test that the hard cap statement is added if missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Plan\n\n## Constraints\nSome constraint.\n")
        temp_path = f.name

    try:
        update_plan_file(temp_path)
        content = Path(temp_path).read_text()
        assert "Max a reasonable number of methods per repository to ensure manageability and coherence." in content
    finally:
        os.unlink(temp_path)

def test_update_plan_adds_total_count():
    """Test that the total count statement is added if missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Plan\n\n## Constraints\nMax a reasonable number of methods per repository to ensure manageability and coherence.\n")
        temp_path = f.name

    try:
        update_plan_file(temp_path)
        content = Path(temp_path).read_text()
        assert "up to 20,000 (20 repos * [deferred])" in content
    finally:
        os.unlink(temp_path)

def test_update_plan_file_not_found():
    """Test that FileNotFoundError is raised if plan.md is missing."""
    with pytest.raises(FileNotFoundError):
        update_plan_file("non_existent_plan.md")
