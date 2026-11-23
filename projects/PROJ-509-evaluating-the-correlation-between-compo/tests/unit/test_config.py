import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import load_paths, load_env


def test_load_paths():
    """Test path loading."""
    paths = load_paths()
    assert "base" in paths
    assert "data" in paths
    assert isinstance(paths["base"], Path)


def test_load_env():
    """Test environment variable loading."""
    env = load_env()
    assert "MPDS_API_KEY" in env
    assert "RANDOM_SEED" in env
    assert isinstance(env["RANDOM_SEED"], str)
