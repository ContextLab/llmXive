"""
Integration test for CPU-only inference pass using microsoft/phi-2.

This test verifies that the StaticScorer can load the model on CPU,
process a small batch of real data (GSM8K), and compute static branching scores
without triggering any CUDA errors or memory allocation failures.

Prerequisites:
  - T007 (download.py) must have successfully downloaded GSM8K to data/raw/
  - T011 (output_schema.yaml) defines the expected structure
  - T016 (static_score/compute.py) implements StaticScorer
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Project root is the parent of the tests directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import get_config, Config
from utils.logger import get_logger
from data.download import download_gsm8k
from static_score.compute import StaticScorer

# Configuration for the test
TEST_MODEL_NAME = "microsoft/phi-2"
TEST_DATASET_NAME = "gsm8k"
TEST_BATCH_SIZE = 2  # Small batch for integration speed
TEST_TIMEOUT_SECONDS = 120  # Max time for model loading + inference

logger = get_logger(__name__)


def ensure_test_data_exists():
    """Ensure the raw GSM8K dataset is downloaded before testing."""
    data_dir = PROJECT_ROOT / "data" / "raw"
    gsm8k_dir = data_dir / "gsm8k"
    
    if not gsm8k_dir.exists():
        logger.info(f"Downloading {TEST_DATASET_NAME} for integration test...")
        download_gsm8k(str(data_dir))
    
    assert gsm8k_dir.exists(), f"Dataset directory {gsm8k_dir} does not exist after download attempt."
    return gsm8k_dir


def load_sample_gsm8k(batch_size: int = 2) -> List[Dict[str, Any]]:
    """Load a small sample of GSM8K tasks."""
    import json
    from pathlib import Path

    data_dir = PROJECT_ROOT / "data" / "raw" / "gsm8k"
    # The download script typically saves as 'train.jsonl' or similar
    # We look for the first available json/jsonl file
    file_path = None
    for ext in ["json", "jsonl", "train.json", "train.jsonl"]:
        candidate = data_dir / ext
        if candidate.exists():
            file_path = candidate
            break
    
    if not file_path:
        # Fallback: try to find any json file
        files = list(data_dir.glob("*.json")) + list(data_dir.glob("*.jsonl"))
        if files:
            file_path = files[0]
    
    if not file_path:
        raise FileNotFoundError(f"No data file found in {data_dir}")

    tasks = []
    with open(file_path, "r", encoding="utf-8") as f:
        # Handle both JSONL and JSON array formats
        if file_path.suffix == ".jsonl":
            for i, line in enumerate(f):
                if i >= batch_size:
                    break
                tasks.append(json.loads(line))
        else:
            data = json.load(f)
            # Handle dict with key or list
            if isinstance(data, dict):
                # Assume key 'train' or similar
                key = next(iter(data.keys()))
                data = data[key]
            for i, item in enumerate(data):
                if i >= batch_size:
                    break
                tasks.append(item)
    
    if not tasks:
        raise ValueError(f"No tasks loaded from {file_path}")
    
    return tasks


@pytest.mark.integration
@pytest.mark.timeout(TEST_TIMEOUT_SECONDS)
def test_cpu_only_inference_pass():
    """
    Integration test: Verify CPU-only inference with microsoft/phi-2.
    
    Steps:
    1. Ensure data is downloaded.
    2. Load a small batch of tasks.
    3. Initialize StaticScorer with device="cpu".
    4. Run scoring on the batch.
    5. Verify output structure and absence of CUDA errors.
    """
    # 1. Ensure data exists
    data_path = ensure_test_data_exists()
    logger.info(f"Data found at {data_path}")

    # 2. Load sample tasks
    tasks = load_sample_gsm8k(batch_size=TEST_BATCH_SIZE)
    logger.info(f"Loaded {len(tasks)} tasks for testing.")

    # 3. Initialize Config and Scorer
    config = get_config()
    config.model_name = TEST_MODEL_NAME
    config.device = "cpu"  # Explicitly force CPU
    config.seed = 42
    
    # Ensure output directory exists
    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "test_static_scores.json"

    scorer = StaticScorer(config)
    
    # 4. Run scoring
    logger.info(f"Starting inference for {TEST_MODEL_NAME} on CPU...")
    try:
        results = scorer.score_batch(tasks, output_path=str(output_file))
    except Exception as e:
        if "CUDA" in str(e) or "cuda" in str(e).lower():
            pytest.fail(f"CUDA error detected during CPU-only inference: {e}")
        raise

    # 5. Verify results
    assert results is not None, "Scoring returned None"
    assert len(results) == len(tasks), f"Expected {len(tasks)} results, got {len(results)}"

    # Verify output file was written
    assert output_file.exists(), f"Output file {output_file} was not created"

    # Verify structure of first result
    first_result = results[0]
    assert "task_id" in first_result, "Missing 'task_id' in result"
    assert "static_scores" in first_result, "Missing 'static_scores' in result"
    assert isinstance(first_result["static_scores"], list), "'static_scores' must be a list"
    
    # Verify no NaNs in scores (basic sanity check)
    import math
    for score in first_result["static_scores"]:
        assert not math.isnan(score), f"NaN detected in score: {score}"

    logger.info("Integration test passed: CPU-only inference successful.")

    # Cleanup test output file
    if output_file.exists():
        os.remove(output_file)


if __name__ == "__main__":
    # Allow running directly with python -m pytest or python script.py
    pytest.main([__file__, "-v"])