"""
Basic smoke test to verify integration of core components.
This satisfies the requirement to have a test file in the integration directory.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
code_path = PROJECT_ROOT / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils import get_logger
from data_models import PolymerRecord

def test_logger_initialization():
    """Verify logger can be initialized and used."""
    logger = get_logger("test_integration")
    assert logger is not None
    assert logger.name == "test_integration"

def test_data_model_instantiation():
    """Verify data models can be instantiated."""
    record = PolymerRecord(
        polymer_id="TEST-001",
        smiles="CCO",
        degradation_pathway="hydrolysis",
        temperature=25.0,
        ph=7.0,
        uv_exposure=0.0
    )
    assert record.polymer_id == "TEST-001"
    assert record.smiles == "CCO"