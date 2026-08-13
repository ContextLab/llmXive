import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

from taxonomy_builder import (
    load_taxonomy,
    build_centroids,
    save_centroids,
    TaxonomyLoadError,
    MemoryLimitExceededError,
)
from config import set_seed

# Mock taxonomy data
MOCK_TAXONOMY = [
    {
        "category": "Safety",
        "description": "Content that causes harm or is dangerous",
    },
    {
        "category": "Privacy",
        "description": "Content that exposes private information",
    },
    {
        "category": "Bias",
        "description": "Content that is discriminatory",
    },
]

@pytest.fixture
def temp_taxonomy_file():
    """Create a temporary taxonomy file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(MOCK_TAXONOMY, f)
    yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_load_taxonomy_valid(temp_taxonomy_file):
    """Test loading a valid taxonomy file."""
    # Temporarily override get_path to return our test file
    import config
    original_get_path = config.get_path

    def mock_get_path(name):
        if name == "raw_taxonomy":
            return Path(temp_taxonomy_file)
        return original_get_path(name)

    config.get_path = mock_get_path

    try:
        taxonomy = load_taxonomy()
        assert isinstance(taxonomy, list)
        assert len(taxonomy) == 3
        assert taxonomy[0]["category"] == "Safety"
    finally:
        config.get_path = original_get_path

def test_load_taxonomy_missing_path():
    """Test that load_taxonomy raises error when path is missing."""
    import config
    original_get_path = config.get_path

    def mock_get_path(name):
        raise KeyError(f"Path '{name}' not found in configuration.")

    config.get_path = mock_get_path

    try:
        with pytest.raises(TaxonomyLoadError) as excinfo:
            load_taxonomy()
        assert "raw_taxonomy" in str(excinfo.value)
    finally:
        config.get_path = original_get_path

def test_load_taxonomy_invalid_json(temp_output_dir):
    """Test that load_taxonomy raises error for invalid JSON."""
    invalid_file = Path(temp_output_dir) / "invalid.json"
    invalid_file.write_text("not valid json")

    import config
    original_get_path = config.get_path

    def mock_get_path(name):
        if name == "raw_taxonomy":
            return invalid_file
        return original_get_path(name)

    config.get_path = mock_get_path

    try:
        with pytest.raises(TaxonomyLoadError):
            load_taxonomy()
    finally:
        config.get_path = original_get_path

def test_build_centroids_basic():
    """Test building centroids with mock data."""
    set_seed(42)
    centroids = build_centroids(MOCK_TAXONOMY, batch_size=2)

    assert isinstance(centroids, dict)
    assert len(centroids) == 3
    assert "Safety" in centroids
    assert "Privacy" in centroids
    assert "Bias" in centroids

    # Check that embeddings are numpy arrays
    for cat, emb in centroids.items():
        assert isinstance(emb, np.ndarray)
        # Check dimensionality (all-MiniLM-L6-v2 produces 384-dim vectors)
        assert emb.shape == (384,)

def test_save_centroids(temp_output_dir):
    """Test saving centroids to JSON."""
    set_seed(42)
    centroids = build_centroids(MOCK_TAXONOMY, batch_size=2)

    output_path = Path(temp_output_dir) / "centroids.json"
    save_centroids(centroids, str(output_path))

    assert output_path.exists()

    # Load and verify
    with open(output_path, "r") as f:
        saved = json.load(f)

    assert "Safety" in saved
    assert "Privacy" in saved
    assert "Bias" in saved

    # Check that values are lists (JSON serializable)
    for cat, emb in saved.items():
        assert isinstance(emb, list)
        assert len(emb) == 384

def test_save_centroids_creates_directory(temp_output_dir):
    """Test that save_centroids creates parent directories if needed."""
    set_seed(42)
    centroids = build_centroids(MOCK_TAXONOMY, batch_size=2)

    # Use a nested path that doesn't exist yet
    output_path = Path(temp_output_dir) / "nested" / "subdir" / "centroids.json"
    save_centroids(centroids, str(output_path))

    assert output_path.exists()
