"""
Basic smoke test to verify pytest is correctly configured and imports work.
This satisfies the requirement to have a test file in the unit directory.
"""
import sys
from pathlib import Path

# Ensure we can import project modules
PROJECT_ROOT = Path(__file__).parent.parent.parent
code_path = PROJECT_ROOT / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

def test_import_data_models():
    """Verify data_models can be imported."""
    from data_models import PolymerRecord, MolecularGraph
    assert PolymerRecord is not None
    assert MolecularGraph is not None

def test_import_utils():
    """Verify utils can be imported."""
    from utils import setup_logging, get_logger
    assert setup_logging is not None
    assert get_logger is not None

def test_import_ingest():
    """Verify ingest can be imported."""
    from ingest import is_valid_smiles
    assert is_valid_smiles is not None

def test_import_setup_project():
    """Verify setup_project can be imported."""
    from setup_project import create_directories
    assert create_directories is not None
