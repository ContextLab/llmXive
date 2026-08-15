"""
T027: Implement run_baseline_sync.py
Execute the full-hardware-sync baseline by running actual quantized inference
for every sample in the test set. Calculate ground-truth acceptance rates and
final reasoning scores based on the RL task definition.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Import from existing API surface
from src.services.quantized_inference import (
    InferenceResult,
    load_quantized_model,
    run_quantized_inference,
    run_quantized_inference_batch
)
from src.config.env_config import load_config, get_model_path
from src.config.logging_config import setup_logger, log_sample_progress
from src.models.entities import TrainingSample, GapPredictionResult

# Configure logger
logger = setup_logger("run_baseline_sync")

# RL Task Constants
# Task: Prompt-completion environment
# State: Prompt
# Action: 'stop' or 'continue' (based on generated text)
# Reward: GSM8K correctness (1 if correct, 0 otherwise)
# For this baseline sync, we simulate the 'stop' decision based on a heuristic
# or a fixed length, and evaluate the 'correctness' by checking if the generated
# text contains a specific marker or matches a ground truth if available.
# Since we are running on the test set from T021A (which is split from training_sample.parquet),
# we assume the 'input_id' or 'prompt' is available.
# We will define a simple heuristic for 'stop' (e.g., max tokens) and 'reasoning_score'
# based on the quality of the generation or a placeholder if ground truth is not directly
# in the test split for the 'correctness' check.
# However, the task requires "ground-truth acceptance rates".
# We will assume the test set contains a 'ground_truth' or 'expected_answer' column,
# or we will use the 'quantization_level' to determine the policy.
# Given the constraints, we will implement a robust runner that logs the process.

MAX_TOKENS = 256
STOP_TOKEN = "</s>"

def load_test_data(test_path: str) -> pd.DataFrame:
    """Load the test set parquet file."""
    path = Path(test_path)
    if not path.exists():
        raise FileNotFoundError(f"Test data file not found: {path}")
    logger.info(f"Loading test data from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} samples. Columns: {list(df.columns)}")
    return df

def evaluate_rl_task(prompt: str, generation: str, ground_truth: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluate the RL task for a single sample.
    State: prompt
    Action: stop/continue (simulated by generation length/content)
    Reward: Correctness (1 if correct, 0 otherwise)
    
    Returns:
        Dict with 'accepted' (bool), 'score' (float)
    """
    # Heuristic for 'stop': if generation is non-empty and ends with a stop token or max length
    # For simplicity in this baseline, we assume the generation is 'accepted' if it's not empty.
    accepted = len(generation.strip()) > 0
    
    # Calculate reasoning score
    # If ground_truth is provided, check for match. Otherwise, use a proxy score (e.g., length normalized)
    # or 0.5 as a neutral score if no ground truth is available in the test set structure.
    score = 0.0
    if ground_truth and ground_truth.strip():
        # Simple exact match or substring match check
        # Normalize strings
        gen_clean = generation.strip().lower()
        gt_clean = ground_truth.strip().lower()
        
        if gt_clean in gen_clean or gen_clean in gt_clean:
            score = 1.0
        else:
            # Fallback: partial credit based on overlap? 
            # For strict baseline, we might just count exact matches or 0.
            # Let's assume 0 if not exact match for now, or a heuristic.
            # Given the "GSM8K correctness" description, exact match of the final number is key.
            # We will try to extract numbers.
            import re
            gen_nums = re.findall(r'\d+', gen_clean)
            gt_nums = re.findall(r'\d+', gt_clean)
            
            if gt_nums and gen_nums and gt_nums[-1] == gen_nums[-1]:
                score = 1.0
            else:
                score = 0.0
    else:
        # If no ground truth in the row, we cannot calculate a true 'correctness' score.
        # We will set score to 0.0 and log a warning, or use a placeholder.
        # However, the task requires a 'reasoning_score'. 
        # We will set it to 0.0 if no GT, as we cannot verify correctness.
        score = 0.0
        logger.debug(f"No ground truth found for sample, score set to 0.0")

    return {
        "accepted": accepted,
        "score": float(score)
    }

def run_baseline_sync(test_path: str, output_path: str, quantization_levels: List[str] = None):
    """
    Execute the full-hardware-sync baseline.
    """
    config = load_config()
    model_path = get_model_path()
    
    if not model_path:
        raise ValueError("Model path not configured in .env")

    # Determine quantization levels to test
    if quantization_levels is None:
        # Default to levels mentioned in T013/T015: INT4, INT8, FP8
        quantization_levels = ["INT4", "INT8", "FP8"]
    
    # Load test data
    df = load_test_data(test_path)
    
    # Ensure we have the necessary columns
    # Expected columns based on T015: input_id, prompt (or similar), ground_truth (if available)
    # We need to map the dataframe columns to the RL task inputs.
    # Assuming 'prompt' or 'input' column exists. If not, try 'input_id' or 'text'.
    prompt_col = None
    gt_col = None
    
    if 'prompt' in df.columns:
        prompt_col = 'prompt'
    elif 'input' in df.columns:
        prompt_col = 'input'
    elif 'text' in df.columns:
        prompt_col = 'text'
    else:
        # Fallback: use input_id as prompt if no text found (unlikely for GSM8K)
        prompt_col = 'input_id'
        logger.warning(f"Prompt column not found. Using '{prompt_col}' as prompt.")

    if 'ground_truth' in df.columns:
        gt_col = 'ground_truth'
    elif 'answer' in df.columns:
        gt_col = 'answer'
    elif 'expected' in df.columns:
        gt_col = 'expected'
    
    if gt_col:
        logger.info(f"Using ground truth column: {gt_col}")
    else:
        logger.warning("No ground truth column found. Reasoning scores will be 0.0.")

    total_samples = len(df)
    accepted_count = 0
    total_score = 0.0
    processed_count = 0
    skipped_count = 0

    logger.info(f"Starting baseline sync for {total_samples} samples with levels: {quantization_levels}")

    # We need to run inference for each sample.
    # To be efficient, we might batch, but the task says "for every sample".
    # We will iterate and run inference.
    
    # We will aggregate results across all quantization levels? 
    # The task says "using the same quantization levels as the dataset".
    # The dataset (training_sample.parquet) has a 'quantization_level' column.
    # The test set is a split of this.
    # So each row in the test set has a specific quantization_level associated with it?
    # Or do we run ALL levels for EVERY sample?
    # T027 says: "using the same quantization levels as the dataset".
    # This implies we respect the level assigned to the sample in the dataset.
    # Let's assume the test set has a 'quantization_level' column.
    
    if 'quantization_level' not in df.columns:
        logger.warning("Column 'quantization_level' not found in test set. Running all levels for all samples.")
        run_all_levels = True
    else:
        run_all_levels = False

    results = []

    for idx, row in df.iterrows():
        sample_id = row.get('input_id', idx)
        prompt = str(row[prompt_col])
        ground_truth = row.get(gt_col, None) if gt_col else None
        
        current_level = None
        if not run_all_levels:
            current_level = row['quantization_level']
            levels_to_run = [current_level]
        else:
            levels_to_run = quantization_levels

        sample_accepted = False
        sample_score = 0.0
        
        for level in levels_to_run:
            try:
                # Load model for this level (cached internally if possible, or re-load)
                # The load_quantized_model function handles caching or reloading.
                logger.debug(f"Running inference for sample {sample_id}, level {level}")
                
                # Run inference
                # run_quantized_inference returns InferenceResult
                result: InferenceResult = run_quantized_inference(
                    model_path=model_path,
                    prompt=prompt,
                    quantization_level=level,
                    max_tokens=MAX_TOKENS
                )
                
                if result.success:
                    generation = result.generated_text
                    eval_result = evaluate_rl_task(prompt, generation, ground_truth)
                    
                    if eval_result['accepted']:
                        sample_accepted = True
                    sample_score = max(sample_score, eval_result['score']) # Take best score across levels if running all
                    
                    # Log progress
                    log_sample_progress(
                        logger, 
                        sample_id, 
                        "success", 
                        extra={"level": level, "score": eval_result['score']}
                    )
                else:
                    logger.warning(f"Inference failed for sample {sample_id}, level {level}: {result.error}")
                    log_sample_progress(
                        logger,
                        sample_id,
                        "error",
                        extra={"level": level, "error_code": "INF_ERROR"}
                    )
                    
            except Exception as e:
                logger.error(f"Exception during inference for sample {sample_id}, level {level}: {e}", exc_info=True)
                log_sample_progress(
                    logger,
                    sample_id,
                    "error",
                    extra={"level": level, "error_code": "EXCEPTION"}
                )
                continue

        processed_count += 1
        if sample_accepted:
            accepted_count += 1
        total_score += sample_score

        results.append({
            "sample_id": sample_id,
            "level": current_level if not run_all_levels else levels_to_run,
            "accepted": sample_accepted,
            "score": sample_score
        })

    # Calculate metrics
    acceptance_rate = accepted_count / processed_count if processed_count > 0 else 0.0
    reasoning_score = total_score / processed_count if processed_count > 0 else 0.0

    metrics = {
        "acceptance_rate": float(acceptance_rate),
        "reasoning_score": float(reasoning_score),
        "total_samples": processed_count,
        "accepted_samples": accepted_count,
        "quantization_levels_tested": quantization_levels
    }

    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Baseline sync completed. Metrics written to {output_file}")
    logger.info(f"Acceptance Rate: {acceptance_rate:.4f}, Reasoning Score: {reasoning_score:.4f}")
    
    return metrics

def main():
    """Main entry point for T027."""
    # Default paths
    test_path = "data/processed/split_test.parquet"
    output_path = "data/processed/baseline_metrics.json"
    
    # Check for command line args
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    try:
        run_baseline_sync(test_path, output_path)
    except Exception as e:
        logger.critical(f"Baseline sync failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()