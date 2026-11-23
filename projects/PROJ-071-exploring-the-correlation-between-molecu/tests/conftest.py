"""
Shared fixtures and configuration for test suite.

This file provides common fixtures used across multiple test modules,
including random seed management, temporary directories, and mock data.
"""

import os
import sys
import random
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session", autouse=True)
def set_random_seeds():
    """Set random seeds for reproducible tests."""
    SEED = 42
    random.seed(SEED)
    np.random.seed(SEED)
    os.environ['PYTHONHASHSEED'] = str(SEED)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_molecule_data():
    """Provide mock molecule data for testing."""
    return [
        {
            "smiles": "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
            "name": "Aspirin",
            "half_life_hours": 12.5
        },
        {
            "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine
            "name": "Caffeine",
            "half_life_hours": 5.2
        },
        {
            "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",  # Ibuprofen
            "name": "Ibuprofen",
            "half_life_hours": 2.1
        }
    ]

@pytest.fixture
def mock_pipeline_result_success():
    """Mock successful pipeline execution result."""
    return {
        "status": "success",
        "data_files": [
            "data/processed/merged_drugs.csv",
            "data/processed/analysis_results.json"
        ],
        "execution_time_seconds": 45.2
    }

@pytest.fixture
def mock_pipeline_result_failure():
    """Mock failed pipeline execution result."""
    return {
        "status": "error",
        "error": "Data availability gate failed: N < 30"
    }

@pytest.fixture
def sample_smiles_list():
    """Provide a list of sample SMILES strings for testing."""
    return [
        "CC(=O)Oc1ccccc1C(=O)O",  # Aspirin
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine
        "CC(C)Cc1ccc(cc1)C(C)C(=O)O",  # Ibuprofen
        "CCN(CC)CCOc1ccc(cc1)CN(C)C",  # Diphenhydramine
        "O=C(O)c1ccccc1C(=O)Nc2ccccc2"  # Acetaminophen analog
    ]

@pytest.fixture
def mock_rdkit_molecule():
    """Create a mock RDKit molecule object."""
    from rdkit import Chem
    smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
    mol = Chem.MolFromSmiles(smiles)
    return mol

@pytest.fixture
def mock_analysis_results():
    """Provide mock analysis results for testing."""
    return {
        "correlation_matrix": {
            "tpsa_vs_half_life": -0.65,
            "mw_vs_half_life": -0.42,
            "rotatable_bonds_vs_half_life": -0.58
        },
        "p_values": {
            "tpsa_vs_half_life": 0.001,
            "mw_vs_half_life": 0.023,
            "rotatable_bonds_vs_half_life": 0.004
        },
        "regression": {
            "coefficients": {
                "tpsa": -0.023,
                "mw": -0.001,
                "rotatable_bonds": -0.15
            },
            "r_squared": 0.72,
            "p_value": 0.0001
        },
        "conclusion": {
            "correlation_exists": True,
            "significant_features": ["tpsa", "rotatable_bonds"]
        }
    }

@pytest.fixture
def mock_config():
    """Provide mock configuration for testing."""
    return {
        "data_paths": {
            "raw": "data/raw",
            "processed": "data/processed",
            "output": "data/outputs"
        },
        "thresholds": {
            "min_samples": 30,
            "correlation_threshold": 0.5,
            "p_value_threshold": 0.05
        },
        "performance": {
            "max_execution_time_seconds": 300
        }
    }

@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to prevent console output during tests."""
    import logging
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
