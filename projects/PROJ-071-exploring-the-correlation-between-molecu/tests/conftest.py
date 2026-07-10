import os
import sys
import random
import numpy as np
import pytest
from pathlib import Path

# Ensure project root is in path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

@pytest.fixture(autouse=True)
def set_seed():
    """
    Fixture to set random seeds for reproducibility across all tests.
    This ensures deterministic behavior for any random operations in tests.
    """
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    yield

@pytest.fixture
def sample_smiles():
    """
    Returns a list of known valid SMILES for testing.
    Includes Aspirin, Caffeine, and Ibuprofen.
    """
    return [
        "CC(=O)OC1=CC=CC=C1C(=O)O",  # Aspirin
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", # Caffeine
        "CC(C)C1=CC=C(C=C1)C(C)C(=O)O" # Ibuprofen
    ]

@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Creates a temporary directory for test outputs.
    Useful for testing file I/O operations without polluting the filesystem.
    """
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

@pytest.fixture
def data_directories(tmp_path):
    """
    Creates the standard project data directory structure in a temporary location.
    Returns a dict with paths to raw, processed, and output directories.
    """
    base_dir = tmp_path / "data"
    raw_dir = base_dir / "raw"
    processed_dir = base_dir / "processed"
    output_dir = base_dir / "outputs"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        "raw": raw_dir,
        "processed": processed_dir,
        "outputs": output_dir,
        "base": base_dir
    }

@pytest.fixture
def mock_fda_dataset(sample_smiles):
    """
    Creates a mock pandas DataFrame mimicking the structure of the FDA dataset
    fetched from HuggingFace. Includes SMILES and degradation columns.
    """
    import pandas as pd
    
    data = {
        "smiles": sample_smiles,
        "drug_name": ["Aspirin", "Caffeine", "Ibuprofen"],
        "degradation_half_life_hours": [24.5, 5.2, 18.0],
        "temperature_c": [25.0, 25.0, 25.0],
        "ph": [7.4, 7.4, 7.4],
        "activation_energy_kj_mol": [50.0, 45.0, 55.0]
    }
    return pd.DataFrame(data)