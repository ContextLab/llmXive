import os
import pytest
from pathlib import Path

def test_quickstart_exists():
    """Verify that quickstart.md exists in the correct location."""
    project_root = Path(__file__).parent.parent.parent
    quickstart_path = project_root / "specs" / "001-llmxive-follow-up-extending-gatemem-benc" / "quickstart.md"
    
    assert quickstart_path.exists(), f"File not found: {quickstart_path}"
    assert quickstart_path.is_file(), f"Not a file: {quickstart_path}"
    
    # Verify file is not empty
    assert quickstart_path.stat().st_size > 0, "quickstart.md is empty"
