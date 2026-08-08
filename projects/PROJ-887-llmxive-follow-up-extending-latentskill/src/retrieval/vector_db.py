"""
Vector Database construction for LatentSkill vectors.

This module implements FR-001: Construct and save the static index
to data/processed/skill_index.npz from flattened LoRA weights.
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import torch

# Import from sibling modules as per project structure
from ..utils.config import get_project_root, get_data_path, ensure_dir
from ..ingestion.flatten_lora import load_flattened_lora


class SkillVectorDB:
    """
    A CPU-compatible static index for skill vectors.

    Stores flattened, normalized LoRA weight vectors and their metadata.
    Uses numpy for zero-dependency CPU storage.
    """

    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize the SkillVectorDB.

        Args:
            index_path: Path to the .npz index file. Defaults to
                       data/processed/skill_index.npz
        """
        self.project_root = get_project_root()
        if index_path is None:
            self.index_path = get_data_path("processed", "skill_index.npz")
        else:
            self.index_path = Path(index_path)

        self.vectors: Optional[np.ndarray] = None
        self.metadata: Optional[List[Dict[str, Any]]] = None
        self.index_map: Optional[np.ndarray] = None  # Maps index -> metadata_id

    def load(self) -> "SkillVectorDB":
        """
        Load the index from disk if it exists.

        Returns:
            self for chaining.

        Raises:
            FileNotFoundError: If the index file does not exist.
        """
        if not self.index_path.exists():
            raise FileNotFoundError(f"Skill index not found at {self.index_path}")

        data = np.load(self.index_path, allow_pickle=True)
        self.vectors = data["vectors"]
        self.metadata = data["metadata"].tolist()
        self.index_map = data["index_map"]
        return self

    def save(self, vectors: np.ndarray, metadata: List[Dict[str, Any]]) -> None:
        """
        Save the vectors and metadata to the static index file.

        Args:
            vectors: Numpy array of shape (N, D) containing flattened skill vectors.
            metadata: List of dicts containing metadata for each vector.
        """
        ensure_dir(self.index_path.parent)

        # Create index map (0 to N-1)
        index_map = np.arange(len(metadata))

        # Save as compressed npz
        np.savez_compressed(
            self.index_path,
            vectors=vectors,
            metadata=np.array(metadata, dtype=object),
            index_map=index_map
        )

        print(f"✓ Saved skill index to {self.index_path}")
        print(f"  - Vectors shape: {vectors.shape}")
        print(f"  - Total entries: {len(metadata)}")

    def query(self, query_vector: np.ndarray, k: int = 5) -> Tuple[np.ndarray, List[Dict]]:
        """
        Perform approximate nearest neighbor search (using brute force for CPU).

        Args:
            query_vector: The query vector (1D array).
            k: Number of nearest neighbors to return.

        Returns:
            Tuple of (similarity_scores, metadata_list)
        """
        if self.vectors is None:
            raise RuntimeError("Index not loaded. Call load() first.")

        # Normalize query vector
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)

        # Compute cosine similarities
        similarities = np.dot(self.vectors, query_norm)

        # Get top-k indices
        top_k_indices = np.argsort(similarities)[::-1][:k]

        return similarities[top_k_indices], [self.metadata[i] for i in top_k_indices]


def construct_skill_index(
    source_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    verbose: bool = True
) -> SkillVectorDB:
    """
    Construct the static skill index from flattened LoRA weights.

    This function:
    1. Loads flattened vectors from the ingestion pipeline (T013 output).
    2. Aggregates them into a single matrix.
    3. Saves the static index to data/processed/skill_index.npz.

    Args:
        source_dir: Directory containing flattened .npz files from T013.
                   Defaults to data/processed/flat_lora_vectors/
        output_path: Path to save the index. Defaults to data/processed/skill_index.npz
        verbose: Whether to print progress logs.

    Returns:
        Constructed SkillVectorDB instance.
    """
    start_time = time.time()

    # Resolve paths
    project_root = get_project_root()
    if source_dir is None:
        source_dir = get_data_path("processed", "flat_lora_vectors")
    else:
        source_dir = Path(source_dir)

    if output_path is None:
        output_path = get_data_path("processed", "skill_index.npz")
    else:
        output_path = Path(output_path)

    if verbose:
        print(f"Constructing skill index from {source_dir}...")

    # Verify source exists
    if not source_dir.exists():
        raise FileNotFoundError(
            f"Source directory for flattened vectors not found: {source_dir}. "
            f"Ensure T013 (flatten_lora.py) has been executed first."
        )

    # Collect all flattened vector files
    vector_files = list(source_dir.glob("*.npz"))
    if not vector_files:
        raise FileNotFoundError(
            f"No .npz files found in {source_dir}. "
            f"Run T013 (flatten_lora.py) to generate flattened vectors first."
        )

    all_vectors = []
    all_metadata = []

    for i, file_path in enumerate(vector_files):
        if verbose:
            print(f"  Loading {file_path.name} ({i+1}/{len(vector_files)})")

        data = np.load(file_path, allow_pickle=True)

        # Extract vectors and metadata
        # Expected keys: 'vectors' (N, D), 'metadata' (list of dicts)
        if 'vectors' not in data:
            raise ValueError(f"Missing 'vectors' key in {file_path.name}")
        if 'metadata' not in data:
            raise ValueError(f"Missing 'metadata' key in {file_path.name}")

        vectors = data['vectors']
        metadata = data['metadata'].tolist() if isinstance(data['metadata'], np.ndarray) else data['metadata']

        # Validate dimensions
        if vectors.ndim != 2:
            raise ValueError(f"Expected 2D vectors in {file_path.name}, got {vectors.ndim}D")

        all_vectors.append(vectors)
        all_metadata.extend(metadata)

    # Concatenate all vectors
    if verbose:
        print(f"  Concatenating {len(all_vectors)} arrays...")

    final_vectors = np.concatenate(all_vectors, axis=0)
    final_metadata = all_metadata

    # Validate
    assert len(final_vectors) == len(final_metadata), "Vector count mismatch with metadata"

    if verbose:
        print(f"  Total vectors: {final_vectors.shape[0]}")
        print(f"  Vector dimension: {final_vectors.shape[1]}")

    # Save the index
    db = SkillVectorDB(index_path=output_path)
    db.save(final_vectors, final_metadata)

    elapsed = time.time() - start_time
    if verbose:
        print(f"✓ Index construction completed in {elapsed:.2f}s")

    return db


def main():
    """
    Entry point for constructing the skill index.
    Usage: python -m src.retrieval.vector_db
    """
    try:
        construct_skill_index()
    except Exception as e:
        print(f"✗ Failed to construct skill index: {e}")
        raise


if __name__ == "__main__":
    main()
