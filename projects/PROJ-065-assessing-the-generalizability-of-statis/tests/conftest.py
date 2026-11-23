"""
Pytest configuration and fixtures for the PROJ-065-assessing-the-generalizability-of-statis project.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure project root is in path for imports
@pytest.fixture(autouse=True)
def setup_paths():
    """Add project root to sys.path to allow imports from code/."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Add code directory to path if not present
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    yield

    # Cleanup (optional)
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))
