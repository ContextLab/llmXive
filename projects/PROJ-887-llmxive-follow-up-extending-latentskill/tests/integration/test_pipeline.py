"""
Integration test for the ingestion pipeline (Task T011).

This test verifies that the full ingestion pipeline (from raw weights to
the final skill index) runs successfully on CPU without requiring GPU resources.
It depends on T013 (flatten_lora) and T014b (vector_db) being implemented.
"""

import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path

import numpy as np
import pytest

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.flatten_lora import flatten_and_normalize_weights
from src.retrieval.vector_db import load_flattened_vectors, compute_index_structure, save_index

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@pytest.fixture
def temp_raw_data_dir():
    """Create a temporary directory with mock raw LoRA weights for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_ingestion_")
    raw_dir = Path(temp_dir) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Create mock LoRA weights (simulating A and B matrices)
    # Dimensions based on T012 spec: in_features=4096, out_features=1024
    # Total flattened size = 4096 * 1024 * 2 (A and B)
    mock_a = np.random.randn(1024, 4096).astype(np.float32)
    mock_b = np.random.randn(4096, 1024).astype(np.float32)

    # Save as .npz (simulating the output of download_weights.py)
    np.savez(raw_dir / "alfworld_weights.npz", A=mock_a, B=mock_b)
    np.savez(raw_dir / "searchqa_weights.npz", A=mock_a, B=mock_b)

    yield raw_dir

    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_processed_dir(temp_raw_data_dir):
    """Create a temporary processed directory."""
    processed_dir = temp_raw_data_dir.parent / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def test_ingestion_pipeline_cpu(temp_raw_data_dir, temp_processed_dir):
    """
    Integration test: Verify the full ingestion pipeline runs on CPU.

    Steps:
    1. Load raw weights from temp directory.
    2. Flatten and normalize using flatten_lora module.
    3. Compute index structure using vector_db module.
    4. Save the index to disk.
    5. Verify the saved index file exists and can be loaded.
    """
    logger.info("Starting ingestion pipeline integration test...")

    # Step 1: Define paths
    raw_weights_path = temp_raw_data_dir
    output_index_path = temp_processed_dir / "skill_index.npz"
    flattened_output_path = temp_processed_dir / "flattened_vectors.npz"

    # Step 2: Flatten and normalize weights (T013)
    logger.info(f"Flattening weights from {raw_weights_path}...")
    # The function expects a directory containing .npz files
    flatten_and_normalize_weights(
        input_dir=raw_weights_path,
        output_file=str(flattened_output_path)
    )

    assert flattened_output_path.exists(), "Flattened vectors file was not created."
    logger.info(f"Flattened vectors saved to {flattened_output_path}")

    # Step 3: Load flattened vectors and compute index (T014a)
    logger.info("Computing index structure...")
    vectors_data = load_flattened_vectors(str(flattened_output_path))
    index_structure = compute_index_structure(vectors_data)

    assert "vectors" in index_structure, "Index structure missing 'vectors' key."
    assert "metadata" in index_structure, "Index structure missing 'metadata' key."
    logger.info(f"Index structure computed with {len(index_structure['metadata'])} entries.")

    # Step 4: Save the index (T014b)
    logger.info(f"Saving index to {output_index_path}...")
    save_index(index_structure, str(output_index_path))

    assert output_index_path.exists(), "Skill index file was not created."
    logger.info(f"Skill index saved to {output_index_path}")

    # Step 5: Verify integrity by loading the saved index
    logger.info("Verifying saved index integrity...")
    loaded_data = np.load(output_index_path, allow_pickle=True)
    loaded_vectors = loaded_data["vectors"]
    loaded_metadata = loaded_data["metadata"].item()

    assert loaded_vectors.shape[0] == len(loaded_metadata), \
        "Mismatch between vector count and metadata entries."
    
    # Verify dimensions (should be 4096 * 1024 * 2 = 8,388,608 per vector)
    expected_dim = 4096 * 1024 * 2
    assert loaded_vectors.shape[1] == expected_dim, \
        f"Vector dimension mismatch. Expected {expected_dim}, got {loaded_vectors.shape[1]}"

    logger.info("Ingestion pipeline integration test PASSED.")
    print(f"SUCCESS: Index generated at {output_index_path}")
    print(f"Vector shape: {loaded_vectors.shape}")
    print(f"Metadata entries: {len(loaded_metadata)}")