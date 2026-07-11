"""
Integration test for "Needle In A Haystack" with heuristic injection.

This test executes a single RULER "Needle In A Haystack" task, comparing
the Exact Match scores of the dense baseline against the gradient magnitude heuristic.

Prerequisites:
- T006: MiniMax wrapper implemented
- T008: Environment config
- T011: Gradient heuristic implemented
- T012: Main entry point implemented

Expected Output:
- Passes if the delta between baseline and heuristic scores is within 2%.
"""
import os
import sys
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.ruler_loader import load_ruler_dataset, ensure_directory
from models.mini_max_wrapper import create_minimax_wrapper, MiniMaxConfig
from heuristics.gradient_magnitude import GradientMagnitudeHeuristic, HeuristicConfig
from utils.logging import setup_logger, HeuristicTimer
from analysis.metrics import calculate_exact_match

logger = setup_logger("integration_test_ruler_run", level=logging.INFO)

def run_single_niah_task(
    model_wrapper,
    task_config: Dict[str, Any],
    heuristic: GradientMagnitudeHeuristic,
    use_heuristic: bool = False
) -> Tuple[str, float]:
    """
    Runs a single Needle In A Haystack task.
    
    Returns:
        Tuple of (predicted_content, exact_match_score)
    """
    # Extract task parameters
    context_length = task_config.get("context_length", 4096)
    needle_content = task_config.get("needle_content", "The answer is 42")
    haystack = task_config.get("haystack", "")
    
    # Construct prompt
    # Assuming a standard RULER prompt format: "Context: ... \n Question: ..."
    prompt = f"Context: {haystack}\n\nQuestion: What is the needle content?\nAnswer:"
    
    logger.info(f"Running Niah task with context length {context_length}")
    
    # Prepare inputs for the model
    # The wrapper handles tokenization internally
    input_ids = model_wrapper.tokenize(prompt)
    
    # Run inference
    with HeuristicTimer("inference_time") as timer:
        if use_heuristic:
            # Inject heuristic logic during generation if supported by wrapper
            # For this integration, we assume the wrapper accepts a hook
            output_ids = model_wrapper.generate(
                input_ids,
                max_new_tokens=20,
                heuristic_callback=heuristic.select_blocks if hasattr(heuristic, 'select_blocks') else None
            )
        else:
            # Dense baseline (no heuristic injection)
            output_ids = model_wrapper.generate(input_ids, max_new_tokens=20)
    
    predicted_text = model_wrapper.detokenize(output_ids)
    
    # Calculate Exact Match
    # Normalize strings for comparison
    target = needle_content.strip().lower()
    prediction = predicted_text.strip().lower()
    
    # Exact match logic: does prediction contain the target?
    # RULER usually expects exact substring match or full string match
    em_score = 1.0 if target in prediction else 0.0
    
    return predicted_text, em_score

def main():
    """
    Main integration test runner.
    
    1. Loads the RULER dataset (or a specific Niah task).
    2. Initializes the MiniMax model (frozen).
    3. Initializes the Gradient Magnitude heuristic.
    4. Runs the task with the dense baseline.
    5. Runs the task with the heuristic injected.
    6. Compares scores and asserts delta <= 2%.
    7. Writes results to data/processed/us1_baseline_vs_heuristic.csv.
    """
    logger.info("Starting Integration Test: T010 - Needle In A Haystack")
    
    # Ensure output directory exists
    output_dir = PROJECT_ROOT / "data" / "processed"
    ensure_directory(output_dir)
    output_file = output_dir / "us1_baseline_vs_heuristic.csv"
    
    # 1. Load Data
    # We expect T004 to have populated data/raw. 
    # If not, we attempt to load the specific Niah task from the dataset.
    try:
        ruler_data = load_ruler_dataset()
        # Filter for a single Niah task for this specific test
        niah_tasks = [t for t in ruler_data if "needle_in_haystack" in t.get("task_name", "").lower()]
        if not niah_tasks:
            # Fallback: construct a minimal Niah task if none found in raw data
            logger.warning("No Niah tasks found in loaded dataset. Generating synthetic Niah task for test.")
            niah_tasks = [{
                "task_id": "niah_synthetic_001",
                "task_name": "needle_in_haystack",
                "context_length": 2048,
                "needle_content": "The secret code is XJ9",
                "haystack": " ".join(["random_word"] * 500) + " The secret code is XJ9 " + " ".join(["random_word"] * 500)
            }]
        
        test_task = niah_tasks[0]
        logger.info(f"Selected task: {test_task['task_id']}")
    except Exception as e:
        logger.error(f"Failed to load Ruler dataset: {e}")
        raise
    
    # 2. Initialize Model
    # T006 ensures we have a wrapper. We assume the model path is set via env or default.
    model_path = os.getenv("MINIMAX_MODEL_PATH", "MiniMaxAI/MiniMax-M3")
    config = MiniMaxConfig(
        model_path=model_path,
        enable_index_branch=False, # As per task requirements
        device="cpu"               # Enforce CPU as per constraints
    )
    
    try:
        model = create_minimax_wrapper(config)
    except Exception as e:
        logger.error(f"Failed to initialize MiniMax wrapper: {e}")
        raise
    
    # 3. Initialize Heuristic
    heuristic_config = HeuristicConfig(
        top_k=10,
        threshold=0.05,
        device="cpu"
    )
    heuristic = GradientMagnitudeHeuristic(heuristic_config)
    
    # 4. Run Baseline (Dense)
    logger.info("Running Baseline (Dense) Inference...")
    baseline_pred, baseline_score = run_single_niah_task(model, test_task, heuristic, use_heuristic=False)
    logger.info(f"Baseline Score: {baseline_score}")
    
    # 5. Run Heuristic Inference
    logger.info("Running Heuristic Inference...")
    heuristic_pred, heuristic_score = run_single_niah_task(model, test_task, heuristic, use_heuristic=True)
    logger.info(f"Heuristic Score: {heuristic_score}")
    
    # 6. Calculate Delta
    delta = abs(baseline_score - heuristic_score)
    tolerance = 0.02 # 2%
    
    logger.info(f"Delta: {delta:.4f}, Tolerance: {tolerance}")
    
    # 7. Assert
    if delta > tolerance:
        logger.error(f"TEST FAILED: Delta {delta} exceeds tolerance {tolerance}")
        # We still write the results, but the test is considered failed
        success = False
    else:
        logger.info("TEST PASSED: Delta within tolerance.")
        success = True
    
    # 8. Write Results
    # Collect timing info if available (mocked or real from wrapper/heuristic)
    # For this test, we assume the wrapper/heuristic logs these or we capture them via the timer context
    # Since we didn't capture specific timer values in the helper above, we log 0.0 or placeholder
    # In a real run, T012 would integrate the timer logic more deeply.
    
    results = {
        "task_id": test_task.get("task_id", "unknown"),
        "baseline_score": baseline_score,
        "heuristic_score": heuristic_score,
        "delta": delta,
        "heuristic_time": 0.0, # Placeholder, to be filled by T012 integration
        "inference_time": 0.0  # Placeholder
    }
    
    file_exists = output_file.exists()
    with open(output_file, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(results)
    
    logger.info(f"Results written to {output_file}")
    
    if not success:
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())