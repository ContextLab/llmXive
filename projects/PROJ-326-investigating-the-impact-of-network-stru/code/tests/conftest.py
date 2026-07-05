"""
Pytest configuration and fixtures.
"""
import os
import random
import tempfile
from pathlib import Path
from typing import Generator
import pytest
import numpy as np
import networkx as nx
from code.src.utils.config import load_config
from code.src.utils.reproducibility import generate_run_id


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def seeded_random_state(seed: int = 42) -> Generator[np.random.RandomState, None, None]:
    """Create a seeded random state for reproducibility."""
    state = np.random.RandomState(seed)
    yield state


@pytest.fixture
def config_fixture(project_root: Path) -> dict:
    """Load the project configuration."""
    config_path = project_root / "code" / "config.yaml"
    if config_path.exists():
        return load_config(config_path)
    return {}


@pytest.fixture
def run_id() -> str:
    """Generate a unique run ID."""
    return generate_run_id()


@pytest.fixture
def sample_graph() -> nx.Graph:
    """Create a small sample graph for testing."""
    G = nx.erdos_renyi_graph(n=10, p=0.3, seed=42)
    return G