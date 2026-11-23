"""
Shared pytest fixtures and configuration for the polymer degradation project.
Implements seed pinning and common test utilities.
"""
import os
import sys
import random
import numpy as np
import pytest
from pathlib import Path
from typing import Generator, Any

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Seed pinning for reproducibility
@pytest.fixture(autouse=True)
def set_seed() -> Generator[None, None, None]:
    """Automatically set random seeds before each test."""
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    # If torch is available, set its seeds
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    
    yield
    
    # Cleanup if needed
    pass

@pytest.fixture
def project_paths() -> dict[str, Path]:
    """Provide standardized project directory paths."""
    return {
        "root": PROJECT_ROOT,
        "code": PROJECT_ROOT / "code",
        "data_raw": PROJECT_ROOT / "data" / "raw",
        "data_processed": PROJECT_ROOT / "data" / "processed",
        "data_reports": PROJECT_ROOT / "data" / "reports",
        "tests": PROJECT_ROOT / "tests",
        "state": PROJECT_ROOT / "state",
    }

@pytest.fixture
def temp_dir(project_paths: dict[str, Path]) -> Generator[Path, None, None]:
    """Create a temporary directory for test artifacts."""
    temp_path = project_paths["root"] / "tests" / "temp"
    temp_path.mkdir(exist_ok=True)
    yield temp_path
    # Cleanup can be added here if needed

@pytest.fixture
def sample_smiles() -> list[str]:
    """Provide a list of valid SMILES strings for testing."""
    return [
        "CC(=O)O",  # Acetic acid (simple ester)
        "CCOC(=O)C",  # Ethyl acetate
        "O=C(O)C1=CC=CC=C1",  # Benzoic acid
        "CC(C)C1=CC=C(C=C1)C(C)C(=O)O",  # Ibuprofen
        "C1=CC=C(C=C1)C(=O)O",  # Benzoic acid
    ]

@pytest.fixture
def invalid_smiles() -> list[str]:
    """Provide a list of invalid SMILES strings for testing."""
    return [
        "invalid_smiles_string",
        "C(C(C",  # Unbalanced parentheses
        "C1C1C1",  # Invalid ring closure
        "",  # Empty string
    ]

@pytest.fixture
def sample_polymer_record(project_paths: dict[str, Path]) -> dict[str, Any]:
    """Provide a sample polymer record for testing."""
    return {
        "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin-like structure
        "temperature": 298.15,
        "ph": 7.0,
        "uv": 0.0,
        "degradation_pathway": "hydrolysis",
        "source_id": "test_record_001",
    }

@pytest.fixture
def mock_graph_data(project_paths: dict[str, Path]) -> dict[str, Any]:
    """Provide mock graph data for testing GNN components."""
    import numpy as np
    return {
        "atom_features": np.random.rand(10, 5).astype(np.float32),
        "bond_features": np.random.rand(15, 3).astype(np.float32),
        "edge_index": np.array([[0, 1, 2, 3], [1, 2, 3, 4]]),
        "environment_vector": np.array([298.15, 7.0, 0.0], dtype=np.float32),
        "label": 0,  # hydrolysis
    }

@pytest.fixture
def log_file_path(project_paths: dict[str, Path]) -> Path:
    """Provide a path for test logging."""
    return project_paths["root"] / "tests" / "test_run.log"

@pytest.fixture(autouse=True)
def setup_test_environment(project_paths: dict[str, Path]) -> Generator[None, None, None]:
    """Ensure test directories exist before running tests."""
    for path in project_paths.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)
    yield
    # Optional: cleanup test artifacts after tests