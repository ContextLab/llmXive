"""
Pytest configuration and fixtures for the project.
Provides shared fixtures for models, data paths, and logging.
"""
import os
import sys
import pytest
from pathlib import Path
import numpy as np
import networkx as nx

# Ensure code directory is in path for imports
@pytest.fixture(autouse=True)
def add_code_to_path(monkeypatch):
    """Add the code directory to sys.path for imports during tests."""
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    
    # Ensure data directories exist for tests that might write
    data_dir = project_root / "data"
    (data_dir / "raw").mkdir(parents=True, exist_ok=True)
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    (data_dir / "contracts").mkdir(parents=True, exist_ok=True)

@pytest.fixture
def sample_snapshot():
    """Create a minimal valid AtomicSnapshot for testing."""
    from models import AtomicSnapshot
    n_atoms = 10
    return AtomicSnapshot(
        species=["Cu"] * 5 + ["Ni"] * 5,
        positions=np.random.rand(n_atoms, 3) * 10.0,
        box=[10.0, 10.0, 10.0],
        metadata={"temperature": 300.0, "thermal_conductivity_W_m_K": 50.0}
    )

@pytest.fixture
def sample_defect_graph():
    """Create a minimal valid DefectGraph for testing."""
    G = nx.Graph()
    # Add nodes with species attributes
    for i in range(10):
        species = "Cu" if i < 5 else "Ni"
        G.add_node(i, species=species)
    
    # Add edges (mismatched species only)
    G.add_edge(0, 5) # Cu-Ni
    G.add_edge(1, 6) # Cu-Ni
    G.add_edge(2, 7) # Cu-Ni
    
    from models import DefectGraph
    return DefectGraph(graph=G)
