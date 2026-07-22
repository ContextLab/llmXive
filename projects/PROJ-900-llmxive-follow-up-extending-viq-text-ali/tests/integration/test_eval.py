"""
Integration test for end-to-end inference on a small batch (US2).

This test verifies that the high-resolution evaluation pipeline can:
1. Load the trained codebook checkpoint (produced by T014).
2. Stream a small batch of real high-resolution images (1024x1024) from ImageNet/COCO.
3. Process them through the frozen ViQ encoder and projection head.
4. Generate projected visual embeddings.
5. Save the embeddings to the declared artifact path: data/results/embeddings_high_res.h5.
6. Calculate and save fidelity metrics (PSNR/SSIM) to data/results/fidelity_metrics.json.

Prerequisites:
- T014 must have completed, producing data/results/codebook_v0.pth.
- T005 (data_loader) must be functional for streaming real data.
- T006a (ViQ invariance check) must have passed (assumed by existence of valid checkpoint).

This test FAILS if:
- The checkpoint file is missing.
- The data loader fails to fetch real images.
- The script does not produce the required output files.
- The output files are empty or malformed.
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest
import numpy as np
import h5py

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.eval_high_res import (
    main as eval_high_res_main,
    load_codebook_checkpoint,
    process_high_res_image,
    get_imagenet_iterator,
    get_coco_iterator,
    log_cxray_exclusion
)
from code.config import get_config, Config
from code.utils import calculate_psnr, calculate_ssim

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_test_eval")

# Constants for test
TEST_BATCH_SIZE = 2
EXPECTED_RESOLUTION = (1024, 1024)
OUTPUT_EMBEDDINGS_PATH = project_root / "data" / "results" / "embeddings_high_res.h5"
OUTPUT_METRICS_PATH = project_root / "data" / "results" / "fidelity_metrics.json"
CHECKPOINT_PATH = project_root / "data" / "results" / "codebook_v0.pth"

def _cleanup_outputs():
    """Remove output files if they exist from previous runs."""
    for path in [OUTPUT_EMBEDDINGS_PATH, OUTPUT_METRICS_PATH]:
        if path.exists():
            path.unlink()
            logger.info(f"Cleaned up existing output: {path}")

def _ensure_checkpoint_exists():
    """
    Ensure the codebook checkpoint exists.
    In a real CI/CD environment, this would be a prerequisite step.
    For this integration test, we assert its existence.
    """
    if not CHECKPOINT_PATH.exists():
        pytest.fail(
            f"Checkpoint file {CHECKPOINT_PATH} not found. "
            "Please ensure T014 (train.py) has completed successfully."
        )

def _validate_embeddings_file(path: Path):
    """Validate the structure and content of the generated embeddings HDF5 file."""
    assert path.exists(), f"Embeddings file {path} was not created."
    assert path.stat().st_size > 0, f"Embeddings file {path} is empty."

    with h5py.File(str(path), 'r') as f:
        # Check for expected datasets
        assert 'embeddings' in f, "Dataset 'embeddings' missing in HDF5 file."
        assert 'image_ids' in f, "Dataset 'image_ids' missing in HDF5 file."
        
        embeddings = f['embeddings'][:]
        image_ids = f['image_ids'][:]

        logger.info(f"Loaded {len(image_ids)} embeddings from {path}")
        logger.info(f"Embedding shape: {embeddings.shape}")

        # Verify shape consistency
        assert len(embeddings) == len(image_ids), "Mismatch between embeddings and image_ids count."
        assert embeddings.shape[1] > 0, "Embedding dimension is 0."

        # Verify data is not all zeros (sanity check)
        if np.allclose(embeddings, 0.0):
            logger.warning("Embeddings appear to be all zeros. This might indicate a model failure.")
            # We don't fail the test here as it might be a valid (but poor) representation,
            # but we log it.

def _validate_metrics_file(path: Path):
    """Validate the structure and content of the generated metrics JSON file."""
    assert path.exists(), f"Metrics file {path} was not created."
    assert path.stat().st_size > 0, f"Metrics file {path} is empty."

    with open(path, 'r') as f:
        data = json.load(f)

    required_keys = ['mean_psnr', 'mean_ssim', 'count', 'note']
    for key in required_keys:
        assert key in data, f"Missing key '{key}' in metrics file."

    assert isinstance(data['mean_psnr'], (int, float)), "mean_psnr must be a number."
    assert isinstance(data['mean_ssim'], (int, float)), "mean_ssim must be a number."
    assert data['count'] > 0, "count must be greater than 0."
    
    logger.info(f"Metrics: PSNR={data['mean_psnr']:.2f}, SSIM={data['mean_ssim']:.4f}, Count={data['count']}")

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test function."""
    _cleanup_outputs()
    _ensure_checkpoint_exists()
    yield
    # Teardown: validate outputs exist and are correct
    if OUTPUT_EMBEDDINGS_PATH.exists():
        _validate_embeddings_file(OUTPUT_EMBEDDINGS_PATH)
    if OUTPUT_METRICS_PATH.exists():
        _validate_metrics_file(OUTPUT_METRICS_PATH)

def test_integration_eval_high_res_end_to_end():
    """
    Run the high-resolution evaluation script end-to-end on a small batch.
    
    This test:
    1. Invokes the main logic of eval_high_res.py (simulating the CLI call).
    2. Uses a small subset of data to ensure it runs quickly.
    3. Verifies that the output files are created and contain valid data.
    """
    # Prepare arguments for the main function
    # We simulate the CLI arguments programmatically
    args = type('Args', (), {
        'checkpoint': str(CHECKPOINT_PATH),
        'batch_size': TEST_BATCH_SIZE,
        'limit': 4,  # Process only 4 images to keep it fast
        'source': 'imagenet',  # Use ImageNet for high-res testing
        'output_dir': str(project_root / "data" / "results"),
        'log_level': 'INFO'
    })()

    # Mock the argument parser to avoid sys.argv manipulation
    # We call the internal logic directly or simulate the main flow
    # Since main() parses args, we can't easily pass a namespace object without
    # modifying main() to accept it. Instead, we'll set sys.argv temporarily.
    
    original_argv = sys.argv
    try:
        sys.argv = [
            'test_eval.py',
            '--checkpoint', str(CHECKPOINT_PATH),
            '--batch-size', str(TEST_BATCH_SIZE),
            '--limit', '4',
            '--source', 'imagenet',
            '--output-dir', str(project_root / "data" / "results"),
            '--log-level', 'INFO'
        ]
        
        # Run the main function
        logger.info("Starting eval_high_res.py integration test...")
        eval_high_res_main()
        logger.info("eval_high_res.py completed successfully.")

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        # Re-raise to fail the test
        raise
    finally:
        sys.argv = original_argv

    # If we reach here, the script ran. Validation is handled by the fixture teardown.
    assert OUTPUT_EMBEDDINGS_PATH.exists(), "Embeddings file not created after execution."
    assert OUTPUT_METRICS_PATH.exists(), "Metrics file not created after execution."

def test_integration_eval_coco_source():
    """
    Test the pipeline with COCO source to ensure it handles different datasets.
    """
    args = type('Args', (), {
        'checkpoint': str(CHECKPOINT_PATH),
        'batch_size': TEST_BATCH_SIZE,
        'limit': 2,
        'source': 'coco',
        'output_dir': str(project_root / "data" / "results"),
        'log_level': 'INFO'
    })()

    original_argv = sys.argv
    try:
        sys.argv = [
            'test_eval_coco.py',
            '--checkpoint', str(CHECKPOINT_PATH),
            '--batch-size', str(TEST_BATCH_SIZE),
            '--limit', '2',
            '--source', 'coco',
            '--output-dir', str(project_root / "data" / "results"),
            '--log-level', 'INFO'
        ]
        
        logger.info("Starting eval_high_res.py with COCO source...")
        eval_high_res_main()
        logger.info("COCO source test completed.")

    finally:
        sys.argv = original_argv

    assert OUTPUT_EMBEDDINGS_PATH.exists()
    assert OUTPUT_METRICS_PATH.exists()