"""
Integration test for SkillVectorDB construction.

Verifies that:
1. The index can be constructed from flattened vectors.
2. The saved index can be loaded.
3. The metadata is preserved correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import numpy as np

import pytest

# Import the module under test
from src.retrieval.vector_db import SkillVectorDB, construct_skill_index
from src.utils.config import get_data_path, ensure_dir


@pytest.fixture
def mock_flattened_vectors(tmp_path):
    """
    Create mock flattened vector files simulating T013 output.
    """
    # Create source directory
    source_dir = tmp_path / "flat_lora_vectors"
    ensure_dir(source_dir)

    # Create mock vector data
    # Simulating 2 adapters with 3 vectors each
    adapter_1_vectors = np.random.randn(3, 128).astype(np.float32)
    adapter_1_metadata = [
        {"id": "skill_1", "task": "alfworld_move", "source": "latent-skills/alfworld-weights"},
        {"id": "skill_2", "task": "alfworld_pick", "source": "latent-skills/alfworld-weights"},
        {"id": "skill_3", "task": "alfworld_place", "source": "latent-skills/alfworld-weights"}
    ]

    adapter_2_vectors = np.random.randn(3, 128).astype(np.float32)
    adapter_2_metadata = [
        {"id": "skill_4", "task": "searchqa_q1", "source": "latent-skills/searchqa-weights"},
        {"id": "skill_5", "task": "searchqa_q2", "source": "latent-skills/searchqa-weights"},
        {"id": "skill_6", "task": "searchqa_q3", "source": "latent-skills/searchqa-weights"}
    ]

    # Save to npz files
    np.savez_compressed(source_dir / "adapter_1.npz", vectors=adapter_1_vectors, metadata=adapter_1_metadata)
    np.savez_compressed(source_dir / "adapter_2.npz", vectors=adapter_2_vectors, metadata=adapter_2_metadata)

    return source_dir


def test_construct_skill_index(mock_flattened_vectors, tmp_path):
    """
    Test that construct_skill_index creates a valid index file.
    """
    output_path = tmp_path / "skill_index.npz"

    # Construct the index
    db = construct_skill_index(
        source_dir=mock_flattened_vectors,
        output_path=output_path,
        verbose=False
    )

    # Verify file exists
    assert output_path.exists(), "Index file was not created"

    # Verify content
    assert db.vectors is not None
    assert db.metadata is not None

    # Check dimensions
    assert db.vectors.shape == (6, 128), f"Expected (6, 128), got {db.vectors.shape}"
    assert len(db.metadata) == 6, f"Expected 6 metadata entries, got {len(db.metadata)}"

    # Verify metadata integrity
    assert db.metadata[0]["id"] == "skill_1"
    assert db.metadata[5]["task"] == "searchqa_q3"


def test_skill_vector_db_load_save(mock_flattened_vectors, tmp_path):
    """
    Test round-trip save and load of SkillVectorDB.
    """
    output_path = tmp_path / "skill_index.npz"

    # Construct
    construct_skill_index(
        source_dir=mock_flattened_vectors,
        output_path=output_path,
        verbose=False
    )

    # Load
    db = SkillVectorDB(index_path=output_path)
    db.load()

    # Verify loaded data matches
    assert db.vectors is not None
    assert db.metadata is not None
    assert db.vectors.shape == (6, 128)
    assert len(db.metadata) == 6


def test_skill_vector_db_query(mock_flattened_vectors, tmp_path):
    """
    Test the query functionality of SkillVectorDB.
    """
    output_path = tmp_path / "skill_index.npz"

    # Construct
    construct_skill_index(
        source_dir=mock_flattened_vectors,
        output_path=output_path,
        verbose=False
    )

    # Load
    db = SkillVectorDB(index_path=output_path)
    db.load()

    # Create a query vector (random)
    query = np.random.randn(128).astype(np.float32)

    # Query
    scores, metadata = db.query(query, k=3)

    # Verify results
    assert len(scores) == 3
    assert len(metadata) == 3
    assert isinstance(scores, np.ndarray)
    assert isinstance(metadata, list)

    # Verify scores are sorted descending
    assert np.all(scores[:-1] >= scores[1:]), "Scores should be sorted descending"