import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'code'))

@pytest.fixture
def sample_polyester_smiles():
    """Provide a sample polyester SMILES string for testing."""
    return 'O=C(OCCOC(=O)c1ccc(C(=O)OCCOC(=O)c2ccc(C(=O)O)cc2)cc1)c3ccc(C(=O)O)cc3'

@pytest.fixture
def sample_non_polyester_smiles():
    """Provide a sample non-polyester SMILES string for testing."""
    return 'CCO'

@pytest.fixture
def sample_records():
    """Provide sample polymer degradation records for testing."""
    return [
        {
            'id': '1',
            'smiles': 'O=C(OCCOC(=O)c1ccc(C(=O)OCCOC(=O)c2ccc(C(=O)O)cc2)cc1)c3ccc(C(=O)O)cc3',
            'temperature': 25,
            'ph': 7.0,
            'uv_intensity': 100,
            'degradation_pathway': 'hydrolysis'
        },
        {
            'id': '2',
            'smiles': 'CCO',
            'temperature': 30,
            'ph': 6.5,
            'uv_intensity': 150,
            'degradation_pathway': 'oxidation'
        }
    ]
