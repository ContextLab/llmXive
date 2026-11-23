import os
import sys
import logging
from pathlib import Path
import pytest

# Add the project root to the path so imports like `code.src...` work
# assuming tests are run from the project root or code directory
@pytest.fixture(autouse=True)
def add_src_to_path():
    project_root = Path(__file__).parent.parent
    # Ensure 'code' directory is in path if it exists
    if (project_root / "code").exists():
        sys.path.insert(0, str(project_root / "code"))
    elif (project_root / "src").exists():
        sys.path.insert(0, str(project_root))
    yield

@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    yield