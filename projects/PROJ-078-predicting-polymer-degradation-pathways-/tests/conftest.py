"""
Pytest configuration and shared fixtures for the Polymer Degradation Pipeline.

This file sets up the testing environment, including:
- Configuring logging to avoid cluttering test output
- Setting up temporary directories for test data
- Providing fixtures for common test data (PolymerRecord, MolecularGraph)
- Mocking external dependencies (RDKit, torch) where necessary for unit tests
"""
import os
import sys
import logging
import tempfile
import pytest
from pathlib import Path
from typing import Generator, Dict, Any, List
from unittest.mock import MagicMock, patch

# Ensure the project root is in the path so imports work correctly
# The project root is assumed to be two levels up from tests/conftest.py
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Configure logging to be quiet during tests by default
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress specific noisy warnings if necessary
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="rdkit")

@pytest.fixture(scope="session")
def temp_project_dir() -> Generator[Path, None, None]:
    """
    Creates a temporary directory structure mimicking the project layout.
    Yields the path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        # Create standard directories
        (base / "code").mkdir()
        (base / "data").mkdir()
        (base / "data" / "raw").mkdir()
        (base / "data" / "processed").mkdir()
        (base / "data" / "reports").mkdir()
        (base / "tests").mkdir()
        (base / "state").mkdir()
        yield base

@pytest.fixture
def sample_smiles_list() -> List[str]:
    """
    Returns a list of valid SMILES strings for testing.
    Includes polyesters and non-polyesters.
    """
    return [
        # Polyesters (contain ester linkages: C(=O)O)
        "CC(=O)OCC", # Ethyl acetate (simple ester)
        "CC(=O)OC1=CC=CC=C1", # Phenyl acetate
        "O=C(O)CC(=O)O", # Succinic acid (dicarboxylic, often part of polyester)
        # Non-polyesters
        "CCO", # Ethanol
        "C1=CC=CC=C1", # Benzene
        "CC(C)C", # Isobutane
    ]

@pytest.fixture
def mock_rdkit_mol() -> MagicMock:
    """
    Returns a mock RDKit Mol object for unit testing logic that depends on RDKit
    without actually importing the heavy library or needing valid chemistry.
    """
    mol = MagicMock()
    mol.GetNumAtoms.return_value = 5
    mol.GetNumBonds.return_value = 4
    mol.GetNumHeavyAtoms.return_value = 4
    mol.GetAtomWithIdx.return_value.GetSymbol.return_value = "C"
    mol.GetBondWithIdx.return_value.GetBondType.return_value = "SINGLE"
    mol.GetBondWithIdx.return_value.GetBeginAtomIdx.return_value = 0
    mol.GetBondWithIdx.return_value.GetEndAtomIdx.return_value = 1
    return mol

@pytest.fixture
def mock_rdkit_chem_module() -> MagicMock:
    """
    Mocks the rdkit.Chem module to allow testing of import-dependent logic
    without requiring a full RDKit installation in the test environment.
    """
    mock_chem = MagicMock()
    mock_chem.MolFromSmiles.return_value = MagicMock()
    mock_chem.MolToSmiles.return_value = "CCO"
    return mock_chem

@pytest.fixture
def mock_torch_geometric() -> MagicMock:
    """
    Mocks torch_geometric modules to prevent heavy imports during unit tests.
    """
    mock_tg = MagicMock()
    mock_tg.data.Data = MagicMock()
    mock_tg.nn.conv.GCNConv = MagicMock()
    mock_tg.nn.pool.global_mean_pool = MagicMock()
    return mock_tg

@pytest.fixture(autouse=True)
def setup_test_environment(temp_project_dir: Path):
    """
    Automatically sets environment variables for the test run to use the
    temporary directory, ensuring no writes go to the real project data.
    """
    os.environ["PROJECT_ROOT"] = str(temp_project_dir)
    os.environ["DATA_RAW_DIR"] = str(temp_project_dir / "data" / "raw")
    os.environ["DATA_PROCESSED_DIR"] = str(temp_project_dir / "data" / "processed")
    os.environ["DATA_REPORTS_DIR"] = str(temp_project_dir / "data" / "reports")
    yield
    # Cleanup is handled by the fixture context manager

# Add a marker for integration tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test requiring external resources."
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow to run."
    )
