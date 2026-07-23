import pytest
import os
import sys
from pathlib import Path

# Add project root to path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield
