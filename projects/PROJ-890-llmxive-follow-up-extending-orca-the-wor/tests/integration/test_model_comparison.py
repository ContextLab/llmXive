"""
Integration test for end-to-end training and stats comparison (T019).

This test verifies the full pipeline for User Story 2:
1. Loads the processed latent vectors and original labels (Descriptive Baseline).
2. Trains the Latent Readout Model (DecisionTree).
3. Trains the Pixel Baseline Model (DecisionTree on simulated downsampled frames).
4. Performs a paired t-test comparing the two models.
5. Asserts that the pipeline completes and outputs valid metrics.

Prerequisites:
- T020a must have generated `data/processed/original_labels.csv`.
- T015 must have generated `data/processed/latents.csv`.
- T024 (baseline_pixel.py) must be implemented.
- T025 (stats.py) must be implemented.
"""
import os
import sys
import csv
import json
import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_config, ensure_directories
from data.models import LatentVectorPydantic
from models.train_readout import train_readout_model
from models.baseline_pixel import train_pixel_baseline
from analysis.stats import perform_paired_ttest

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_model_comparison")

# --- Helper Functions for Test Data Generation ---
# Since T020a and T015 are prerequisites, we simulate the existence of
# their output files here to ensure this test is self-contained and runnable
# in an integration context without blocking on external data fetches during the test run.
# In a real CI/CD pipeline, these files would be produced by previous stages.

def _generate_mock_latents_csv(output_path: Path, n_samples: int = 50):
    """Generates a mock latents.csv for testing purposes."""
    logger.info(f"Generating mock latents.csv with {n_samples} samples at {output_path}")
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        # Header: video_id, prompt, latent_vector (JSON string)
        writer.writerow(["video_id", "prompt", "latent_vector"])
        for i in range(n_samples):
            video_id = f"clip_{i:04d}"
            prompt = "The object falls to the ground."
            # Simulate a latent vector of dimension 768 (common for Orca-like models)
            latent_vec = np.random.randn(768).tolist()
            writer.writerow([video_id, prompt, json.dumps(latent_vec)])
    logger.info("Mock latents.csv generated.")

def _generate_mock_original_labels_csv(output_path: Path, n_samples: int = 50):
    """Generates a mock original_labels.csv for testing purposes."""
    logger.info(f"Generating mock original_labels.csv with {n_samples} samples at {output_path}")
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        # Header: scenario_id, original_outcome
        writer.writerow(["scenario_id", "original_outcome"])
        for i in range(n_samples):
            scenario_id = f"clip_{i:04d}"
            # Binary outcome: 1 for "fell", 0 for "stayed"
            outcome = 1 if i % 2 == 0 else 0
            writer.writerow([scenario_id, outcome])
    logger.info("Mock original_labels.csv generated.")

def _generate_mock_frames_cache(output_path: Path, n_samples: int = 50):
    """Generates a mock cache of downsampled frames for the pixel baseline."""
    # We create a simple NPY file mapping video_id to (T, H, W, C) array
    # Shape: (50, 3, 32, 32, 3) -> 50 samples, 3 frames, 32x32, RGB
    logger.info(f"Generating mock frame cache with {n_samples} samples at {output_path}")
    data = np.random.rand(n_samples, 3, 32, 32, 3).astype(np.float32)
    np.save(output_path, data)
    logger.info("Mock frame cache generated.")

# --- Main Test Logic ---

def test_end_to_end_training_and_comparison():
    """
    Runs the full training and comparison pipeline.
    """
    # 1. Setup temporary directory for test artifacts
    temp_dir = tempfile.mkdtemp(prefix="orca_test_integration_")
    temp_path = Path(temp_dir)
    
    try:
        # Ensure data directories exist (simulating T008)
        ensure_directories()
        
        # Define paths for mock data
        latents_path = temp_path / "latents.csv"
        labels_path = temp_path / "original_labels.csv"
        frames_cache_path = temp_path / "frame_cache.npy"
        output_metrics_path = temp_path / "comparison_results.json"
        
        # 2. Generate mock prerequisite data (T015, T020a)
        _generate_mock_latents_csv(latents_path, n_samples=50)
        _generate_mock_original_labels_csv(labels_path, n_samples=50)
        _generate_mock_frames_cache(frames_cache_path, n_samples=50)
        
        # 3. Prepare arguments for training scripts
        # Note: In a real scenario, these paths would point to data/processed/
        # We use temp paths here to avoid dependency on actual file system state
        config = get_config()
        
        # --- Step A: Train Latent Model (T023) ---
        logger.info("Starting Latent Model Training...")
        try:
            latent_metrics = train_readout_model(
                latents_path=str(latents_path),
                labels_path=str(labels_path),
                output_path=str(temp_path / "latent_model_metrics.json"),
                model_type="decision_tree",
                test_size=0.2,
                random_state=42
            )
            logger.info(f"Latent Model Training Complete. Accuracy: {latent_metrics.get('accuracy', 'N/A')}")
        except Exception as e:
            logger.error(f"Latent Model Training Failed: {e}")
            raise

        # --- Step B: Train Pixel Baseline (T024) ---
        logger.info("Starting Pixel Baseline Training...")
        try:
            pixel_metrics = train_pixel_baseline(
                frames_cache_path=str(frames_cache_path),
                labels_path=str(labels_path),
                output_path=str(temp_path / "pixel_model_metrics.json"),
                model_type="decision_tree",
                test_size=0.2,
                random_state=42
            )
            logger.info(f"Pixel Baseline Training Complete. Accuracy: {pixel_metrics.get('accuracy', 'N/A')}")
        except Exception as e:
            logger.error(f"Pixel Baseline Training Failed: {e}")
            raise

        # --- Step C: Perform Statistical Comparison (T025) ---
        logger.info("Performing Statistical Comparison...")
        try:
            # We simulate the t-test by comparing the metrics from the two models
            # In a real run, this would compare cross-validation folds
            t_stat, p_value = perform_paired_ttest(
                model_a_metrics=latent_metrics,
                model_b_metrics=pixel_metrics
            )
            logger.info(f"Statistical Comparison Complete. t-stat: {t_stat:.4f}, p-value: {p_value:.4f}")
        except Exception as e:
            logger.error(f"Statistical Comparison Failed: {e}")
            raise

        # --- Step D: Assertions ---
        assert "accuracy" in latent_metrics, "Latent model metrics missing accuracy"
        assert "accuracy" in pixel_metrics, "Pixel model metrics missing accuracy"
        assert isinstance(p_value, float), "p-value must be a float"
        assert 0.0 <= p_value <= 1.0, "p-value must be between 0 and 1"
        
        logger.info("✅ Integration Test PASSED: End-to-end training and comparison successful.")
        
    finally:
        # Cleanup
        if temp_path.exists():
            shutil.rmtree(temp_path)
            logger.info("Temporary directory cleaned up.")

if __name__ == "__main__":
    test_end_to_end_training_and_comparison()
    print("Integration test T019 completed successfully.")