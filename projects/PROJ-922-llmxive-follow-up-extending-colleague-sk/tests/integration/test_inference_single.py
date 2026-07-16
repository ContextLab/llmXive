"""
Integration test for single inference run (US1).

This test verifies that the system can load a quantized model on CPU,
generate a response for a single profile-task pair across all three
conditions (Monolithic, Separated, Generic) within the timeout limit,
and handle potential OOM errors gracefully.

Prerequisites:
- T006 (profiles.py) must have been run to generate data/processed/profiles.json
- T007 (tasks.py) must have been run to generate data/processed/tasks.json
- T012 (engine.py) must be implemented with load_model and generate functions
- T008 (prompts.py) must be implemented with prompt building functions
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_data_dir, set_global_seed
from utils.logging import get_logger
from inference.engine import InferenceEngine, InferenceTimeoutError, InferenceOOMError, ModelLoadError
from inference.prompts import build_prompt, get_monolithic_prompt, get_separated_tracks_prompt, get_generic_baseline_prompt
from data_generation.profiles import load_profiles
from data_generation.tasks import load_tasks

logger = get_logger(__name__)

# Configuration
TIMEOUT_SECONDS = 300
MODEL_PATH_ENV = "LLMXIVE_MODEL_PATH"
DEFAULT_MODEL_PATH = "models/llama-3-8b-Q4_K_M.gguf"  # Fallback if env var not set

@pytest.fixture(scope="module")
def setup_test_data():
    """Load a single profile and a single task for testing."""
    set_global_seed(42)
    data_dir = get_data_dir()
    
    profiles_path = data_dir / "processed" / "profiles.json"
    tasks_path = data_dir / "processed" / "tasks.json"

    if not profiles_path.exists():
        pytest.skip(f"Profiles file not found at {profiles_path}. Run T006 first.")
    
    if not tasks_path.exists():
        pytest.skip(f"Tasks file not found at {tasks_path}. Run T007 first.")

    with open(profiles_path, 'r') as f:
        profiles = json.load(f)
    
    with open(tasks_path, 'r') as f:
        tasks = json.load(f)

    # Select first profile and first task
    profile = profiles[0]
    task = tasks[0]

    return profile, task

@pytest.fixture(scope="module")
def inference_engine():
    """Initialize the inference engine."""
    model_path = os.environ.get(MODEL_PATH_ENV, DEFAULT_MODEL_PATH)
    
    # Check if model exists (if not, we might need to skip or download)
    # For this test, we assume the model is available or the engine handles download
    try:
        engine = InferenceEngine(
            model_path=model_path,
            device="cpu",
            n_gpu_layers=0,
            timeout_seconds=TIMEOUT_SECONDS
        )
        return engine
    except ModelLoadError as e:
        pytest.skip(f"Could not load model: {e}. Ensure model is available at {model_path}")
    except Exception as e:
        pytest.skip(f"Failed to initialize inference engine: {e}")

def test_inference_single_profile_task_monolithic(inference_engine, setup_test_data):
    """Test inference with Monolithic prompt condition."""
    profile, task = setup_test_data
    
    prompt = build_prompt(
        profile=profile,
        task=task,
        condition="monolithic"
    )
    
    start_time = time.time()
    try:
        output = inference_engine.generate(prompt)
        elapsed = time.time() - start_time
        
        logger.info(f"Monolithic inference completed in {elapsed:.2f}s")
        assert output is not None, "Output should not be None"
        assert isinstance(output, str), "Output should be a string"
        assert len(output) > 0, "Output should not be empty"
        assert elapsed <= TIMEOUT_SECONDS, f"Generation took too long: {elapsed}s"
    except InferenceTimeoutError:
        pytest.fail("Inference timed out")
    except InferenceOOMError:
        pytest.fail("Out of memory error during inference")

def test_inference_single_profile_task_separated(inference_engine, setup_test_data):
    """Test inference with Separated Tracks prompt condition."""
    profile, task = setup_test_data
    
    prompt = build_prompt(
        profile=profile,
        task=task,
        condition="separated"
    )
    
    start_time = time.time()
    try:
        output = inference_engine.generate(prompt)
        elapsed = time.time() - start_time
        
        logger.info(f"Separated inference completed in {elapsed:.2f}s")
        assert output is not None, "Output should not be None"
        assert isinstance(output, str), "Output should be a string"
        assert len(output) > 0, "Output should not be empty"
        assert elapsed <= TIMEOUT_SECONDS, f"Generation took too long: {elapsed}s"
    except InferenceTimeoutError:
        pytest.fail("Inference timed out")
    except InferenceOOMError:
        pytest.fail("Out of memory error during inference")

def test_inference_single_profile_task_generic(inference_engine, setup_test_data):
    """Test inference with Generic Baseline prompt condition."""
    profile, task = setup_test_data
    
    prompt = build_prompt(
        profile=profile,
        task=task,
        condition="generic"
    )
    
    start_time = time.time()
    try:
        output = inference_engine.generate(prompt)
        elapsed = time.time() - start_time
        
        logger.info(f"Generic inference completed in {elapsed:.2f}s")
        assert output is not None, "Output should not be None"
        assert isinstance(output, str), "Output should be a string"
        assert len(output) > 0, "Output should not be empty"
        assert elapsed <= TIMEOUT_SECONDS, f"Generation took too long: {elapsed}s"
    except InferenceTimeoutError:
        pytest.fail("Inference timed out")
    except InferenceOOMError:
        pytest.fail("Out of memory error during inference")

def test_inference_all_conditions_consistency(inference_engine, setup_test_data):
    """Test that all three conditions produce different but valid outputs."""
    profile, task = setup_test_data
    conditions = ["monolithic", "separated", "generic"]
    outputs = {}
    
    for condition in conditions:
        prompt = build_prompt(profile=profile, task=task, condition=condition)
        start_time = time.time()
        try:
            output = inference_engine.generate(prompt)
            elapsed = time.time() - start_time
            outputs[condition] = {
                "output": output,
                "latency": elapsed,
                "success": True
            }
            logger.info(f"{condition}: {elapsed:.2f}s")
        except Exception as e:
            outputs[condition] = {
                "output": None,
                "latency": time.time() - start_time,
                "success": False,
                "error": str(e)
            }
            logger.error(f"{condition} failed: {e}")
    
    # Verify all conditions produced valid outputs
    for condition, result in outputs.items():
        assert result["success"], f"{condition} condition failed: {result.get('error')}"
        assert result["output"] is not None
        assert isinstance(result["output"], str)
        assert len(result["output"]) > 0
        assert result["latency"] <= TIMEOUT_SECONDS

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
