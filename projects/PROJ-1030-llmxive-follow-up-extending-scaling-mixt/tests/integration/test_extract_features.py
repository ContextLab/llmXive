"""
Integration test for feature extraction flow (User Story 1).

This test verifies the end-to-end flow of:
1. Downloading/Loading the LingBot-Video model (simulated via mock if offline, but structure matches real)
2. Streaming/Loading video clips
3. Extracting latent activation vectors and expert masks
4. Saving results to data/processed/features.npy and data/processed/features_metadata.json

It ensures the pipeline runs within memory constraints and produces valid artifacts.
"""
import os
import sys
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import get_logger
from utils.memory_manager import calculate_max_frames, generate_temporal_chunks
from utils.error_handler import DataFetchError, retry_with_backoff

logger = get_logger(__name__)

# Constants for test configuration
TEST_OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
TEST_FEATURES_FILE = TEST_OUTPUT_DIR / "features.npy"
TEST_METADATA_FILE = TEST_OUTPUT_DIR / "features_metadata.json"

# Mock model configuration matching the expected LingBot-Video structure
MOCK_MODEL_CONFIG = {
    "hidden_size": 768,
    "num_layers": 24,
    "num_heads": 12,
    "expert_dim": 1536,
    "num_experts": 8,
    "active_experts_per_token": 2
}

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup test environment and clean up after."""
    # Ensure output directory exists
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean up any existing test artifacts
    if TEST_FEATURES_FILE.exists():
        TEST_FEATURES_FILE.unlink()
    if TEST_METADATA_FILE.exists():
        TEST_METADATA_FILE.unlink()
        
    yield
    
    # Teardown: Clean up test artifacts
    if TEST_FEATURES_FILE.exists():
        TEST_FEATURES_FILE.unlink()
    if TEST_METADATA_FILE.exists():
        TEST_METADATA_FILE.unlink()

def test_feature_extraction_pipeline():
    """
    Integration test: Verify the full feature extraction pipeline runs
    and produces valid output files.
    """
    logger.info("Starting integration test for feature extraction pipeline")
    
    # Mock the model loading and video data fetching to ensure reproducibility
    # without requiring actual large downloads during CI/testing
    with patch('code.extract_features.load_model') as mock_load_model, \
         patch('code.extract_features.load_video_clips') as mock_load_clips, \
         patch('code.extract_features.extract_activations') as mock_extract:
        
        # Setup mocks
        mock_model = MagicMock()
        mock_model.config = MagicMock(**MOCK_MODEL_CONFIG)
        mock_load_model.return_value = mock_model
        
        # Simulate a small batch of video clips (3 clips for testing)
        mock_clips = [
            {"id": "clip_001", "frames": np.random.rand(16, 224, 224, 3).astype(np.float32)},
            {"id": "clip_002", "frames": np.random.rand(16, 224, 224, 3).astype(np.float32)},
            {"id": "clip_003", "frames": np.random.rand(16, 224, 224, 3).astype(np.float32)}
        ]
        mock_load_clips.return_value = mock_clips
        
        # Simulate extracted features: (num_clips, num_frames, hidden_size)
        # and expert masks: (num_clips, num_frames, num_experts)
        num_clips = 3
        num_frames = 16
        hidden_size = MOCK_MODEL_CONFIG["hidden_size"]
        num_experts = MOCK_MODEL_CONFIG["num_experts"]
        
        mock_latents = np.random.rand(num_clips, num_frames, hidden_size).astype(np.float32)
        mock_masks = np.random.randint(0, 2, (num_clips, num_frames, num_experts)).astype(np.float32)
        
        mock_extract.return_value = (mock_latents, mock_masks)
        
        # Import and run the actual extraction script
        # We import here to ensure mocks are in place
        import importlib.util
        spec = importlib.util.spec_from_file_location("extract_features", PROJECT_ROOT / "code" / "extract_features.py")
        extract_module = importlib.util.module_from_spec(spec)
        
        # We need to mock the main function execution logic
        # Since the script runs directly, we simulate the call
        with patch.object(extract_module, 'main') as mock_main:
            mock_main.return_value = True
            spec.loader.exec_module(extract_module)
            # Simulate calling the main function
            extract_module.main()
    
    # Assertions: Verify output files were created
    assert TEST_FEATURES_FILE.exists(), "Feature file (features.npy) was not created"
    assert TEST_METADATA_FILE.exists(), "Metadata file (features_metadata.json) was not created"
    
    # Verify feature file content
    loaded_features = np.load(TEST_FEATURES_FILE)
    assert loaded_features.shape == (num_clips, num_frames, hidden_size), \
        f"Unexpected feature shape: {loaded_features.shape}"
    assert loaded_features.dtype == np.float32, f"Unexpected dtype: {loaded_features.dtype}"
    assert not np.all(loaded_features == 0), "Features are all zeros - extraction likely failed"
    
    # Verify metadata content
    with open(TEST_METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    assert "model_config" in metadata, "Missing model_config in metadata"
    assert "extraction_stats" in metadata, "Missing extraction_stats in metadata"
    assert "clip_ids" in metadata, "Missing clip_ids in metadata"
    
    assert len(metadata["clip_ids"]) == num_clips, "Clip count mismatch"
    assert metadata["extraction_stats"]["total_clips"] == num_clips, "Stats mismatch"
    
    logger.info("Integration test passed: Feature extraction pipeline produced valid artifacts")

def test_memory_constraints_handling():
    """
    Integration test: Verify memory management logic is invoked correctly.
    """
    logger.info("Testing memory constraint handling")
    
    # Test memory calculation logic
    frame_size = 224 * 224 * 3 * 4  # H*W*C*bytes_per_float
    max_frames = calculate_max_frames(frame_size, max_ram_gb=7.0)
    
    assert max_frames > 0, "Max frames calculation failed"
    assert max_frames < 1000, "Max frames calculation seems too high for 7GB limit"
    
    # Test temporal chunking
    total_frames = 100
    chunk_size = max_frames
    chunks = generate_temporal_chunks(total_frames, chunk_size)
    
    assert len(chunks) > 0, "No chunks generated"
    assert sum(len(c) for c in chunks) == total_frames, "Frame count mismatch after chunking"
    
    logger.info("Memory constraint handling test passed")

def test_error_handling_on_data_fetch():
    """
    Integration test: Verify that the pipeline fails loudly on data fetch errors.
    """
    logger.info("Testing error handling for data fetch failures")
    
    with patch('code.extract_features.load_video_clips') as mock_load_clips:
        mock_load_clips.side_effect = DataFetchError("Simulated network failure")
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("extract_features", PROJECT_ROOT / "code" / "extract_features.py")
        extract_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extract_module)
        
        with pytest.raises(DataFetchError):
            extract_module.main()
    
    logger.info("Error handling test passed: Pipeline correctly raises on data fetch failure")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
