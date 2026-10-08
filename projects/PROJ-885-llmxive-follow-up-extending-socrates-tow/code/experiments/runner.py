"""
CPU-only Inference Runner for Socio-Cognitive State Injection Experiments.

This module implements the core experiment execution loop, enforcing CPU-only
execution, managing model loading, and handling dynamic state injection.
"""

import json
import logging
import time
import uuid
import torch
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import ensure_directories, setup_logging, get_config_summary
from data.generator import split_trajectory_into_turns, derive_classifier_training_data
from models.classifier import SocioCognitiveClassifier
from experiments.prompts import get_static_baseline_prompt, get_dynamic_adapter_prompt
from experiments.retry_utils import exponential_backoff_retry
from analysis.log_writer import write_experiment_logs

# Constants
CONFIDENCE_THRESHOLD = 0.65  # Threshold for low-confidence fallback
NEUTRAL_STATE_LABEL = "neutral-monitoring"

logger = logging.getLogger(__name__)

def enforce_cpu_only_execution(model_name: str) -> Optional[str]:
    """
    Enforce CPU-only execution policy.
    
    If GPU is available, this function logs a warning, appends an exclusion
    record to scope_adjustments.json, and returns None to indicate the model
    should be skipped.
    
    Args:
        model_name: Name of the model being loaded.
        
    Returns:
        None if GPU detected (model excluded), otherwise returns 'cpu'.
    """
    if torch.cuda.is_available():
        warning_msg = f"GPU detected ({torch.cuda.device_count()} devices). Excluding model '{model_name}' to ensure CPU-only reproducibility."
        logger.warning(warning_msg)
        
        # Prepare exclusion record
        exclusion_record = {
            "model_name": model_name,
            "reason": "GPU_detected",
            "estimated_ram_gb": None
        }
        
        # Append to scope_adjustments.json
        scope_file = Path("data/results/scope_adjustments.json")
        ensure_directories()
        
        # Load existing records or initialize
        try:
            if scope_file.exists():
                with open(scope_file, 'r') as f:
                    records = json.load(f)
            else:
                records = []
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read scope_adjustments.json: {e}")
            records = []
        
        # Append new record
        records.append(exclusion_record)
        
        # Write back
        with open(scope_file, 'w') as f:
            json.dump(records, f, indent=2)
        
        logger.info(f"Exclusion record for '{model_name}' appended to {scope_file}")
        return None
    
    return "cpu"

def load_classifier() -> SocioCognitiveClassifier:
    """
    Load the pre-trained classifier for state detection.
    
    Returns:
        Initialized SocioCognitiveClassifier instance.
    """
    classifier_path = Path("data/processed/classifier_model.pkl")
    
    if not classifier_path.exists():
        raise FileNotFoundError(
            f"Classifier model not found at {classifier_path}. "
            "Please run T020 (classifier training) before T027."
        )
    
    logger.info(f"Loading classifier from {classifier_path}")
    classifier = SocioCognitiveClassifier.load(classifier_path)
    return classifier

def run_single_turn_inference(
    model, 
    tokenizer, 
    prompt: str, 
    max_length: int = 512
) -> str:
    """
    Run a single turn of inference on the loaded model.
    
    Args:
        model: The loaded transformer model.
        tokenizer: The corresponding tokenizer.
        prompt: The input prompt text.
        max_length: Maximum sequence length for generation.
        
    Returns:
        Generated text response.
    """
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length)
    inputs = {k: v.to("cpu") for k, v in inputs.items()}  # Explicitly move to CPU
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Remove the original prompt from the response
    response = response.replace(prompt, "").strip()
    return response

def get_state_for_turn(
    classifier: SocioCognitiveClassifier, 
    turn_text: str
) -> Tuple[str, float]:
    """
    Get the socio-cognitive state for a given turn text using the classifier.
    
    Args:
        classifier: The trained classifier.
        turn_text: The dialogue turn text.
        
    Returns:
        Tuple of (state_label, confidence_score).
    """
    state_label, confidence = classifier.predict_with_confidence(turn_text)
    return state_label, confidence

def process_trajectory(
    trajectory: Dict[str, Any],
    model,
    tokenizer,
    classifier: SocioCognitiveClassifier,
    condition: str,
    model_name: str
) -> List[Dict[str, Any]]:
    """
    Process a single conflict trajectory through the LLM under the specified condition.
    
    Args:
        trajectory: The conflict trajectory data.
        model: The loaded LLM.
        tokenizer: The LLM tokenizer.
        classifier: The state classifier.
        condition: Either 'adapter' or 'static'.
        model_name: Name of the model being used.
        
    Returns:
        List of turn-level experiment logs.
    """
    log_entries = []
    turns = split_trajectory_into_turns(trajectory)
    
    # Accumulator for dialogue history
    dialogue_history = []
    
    for i, turn in enumerate(turns):
        turn_text = turn.get("text", "")
        dialogue_history.append(turn_text)
        
        # Build prompt based on condition
        if condition == "adapter":
            # Get state for current turn
            state_label, confidence = get_state_for_turn(classifier, turn_text)
            
            # Determine injected state
            if confidence < CONFIDENCE_THRESHOLD:
                injected_state = NEUTRAL_STATE_LABEL
                prompt_template = get_static_baseline_prompt(turn_text)  # Fallback to static
            else:
                injected_state = state_label
                prompt_template = get_dynamic_adapter_prompt(turn_text, injected_state)
            
            full_prompt = prompt_template
        else:
            # Static condition: no injection
            injected_state = None
            confidence = None
            full_prompt = get_static_baseline_prompt(turn_text)
        
        # Run inference
        try:
            response = run_single_turn_inference(model, tokenizer, full_prompt)
            status = "success"
        except Exception as e:
            logger.error(f"Inference failed for turn {i}: {e}")
            response = "[INFERENCE_ERROR]"
            status = "error"
        
        # Create log entry
        log_entry = {
            "trajectory_id": trajectory.get("id"),
            "turn_index": i,
            "turn_text": turn_text,
            "model_name": model_name,
            "condition": condition,
            "prompt": full_prompt[:500] + "..." if len(full_prompt) > 500 else full_prompt,
            "response": response,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence_score": confidence,
            "injected_state": injected_state,
            "metadata": {
                "condition_details": "adapter" if condition == "adapter" else "static_baseline"
            }
        }
        
        log_entries.append(log_entry)
    
    return log_entries

def run_experiment(
    trajectories: List[Dict[str, Any]],
    model_name: str,
    model,
    tokenizer,
    classifier: SocioCognitiveClassifier,
    conditions: List[str]
) -> List[Dict[str, Any]]:
    """
    Run the full experiment suite for a given model and set of trajectories.
    
    Args:
        trajectories: List of conflict trajectories.
        model_name: Name of the model.
        model: The loaded model.
        tokenizer: The model tokenizer.
        classifier: The state classifier.
        conditions: List of conditions to run (e.g., ['adapter', 'static']).
        
    Returns:
        Aggregated list of all experiment log entries.
    """
    all_logs = []
    
    for trajectory in trajectories:
        for condition in conditions:
            logger.info(f"Processing trajectory {trajectory.get('id')} with {model_name} under {condition} condition")
            start_time = time.time()
            
            turn_logs = process_trajectory(
                trajectory=trajectory,
                model=model,
                tokenizer=tokenizer,
                classifier=classifier,
                condition=condition,
                model_name=model_name
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Completed {condition} condition in {elapsed:.2f}s")
            
            all_logs.extend(turn_logs)
    
    return all_logs

def main():
    """
    Main entry point for the experiment runner.
    
    Usage: python code/experiments/runner.py --models <model1,model2> --conditions <cond1,cond2>
    """
    setup_logging()
    logger.info("Starting CPU-only Inference Runner")
    
    # Parse arguments (simplified for this task)
    import argparse
    parser = argparse.ArgumentParser(description="Run inference experiments")
    parser.add_argument("--models", type=str, default="llama-3-8b-instruct", 
                      help="Comma-separated list of model names")
    parser.add_argument("--conditions", type=str, default="adapter,static",
                      help="Comma-separated list of conditions")
    args = parser.parse_args()
    
    model_names = [m.strip() for m in args.models.split(",")]
    conditions = [c.strip() for c in args.conditions.split(",")]
    
    logger.info(f"Models to run: {model_names}")
    logger.info(f"Conditions to run: {conditions}")
    
    # Load classifier
    try:
        classifier = load_classifier()
        logger.info("Classifier loaded successfully")
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    
    # Load trajectories (simplified - in real scenario, load from data/processed/trajectories.json)
    trajectories_path = Path("data/processed/trajectories.json")
    if not trajectories_path.exists():
        logger.error(f"Trajectories file not found at {trajectories_path}")
        return 1
    
    with open(trajectories_path, 'r') as f:
        trajectories = json.load(f)
    
    logger.info(f"Loaded {len(trajectories)} trajectories")
    
    # Import model loader here to avoid circular imports
    from experiments.model_loader import check_and_load_model
    
    all_experiment_logs = []
    
    for model_name in model_names:
        logger.info(f"Processing model: {model_name}")
        
        # Enforce CPU-only
        device = enforce_cpu_only_execution(model_name)
        if device is None:
            # Model was excluded due to GPU detection
            continue
        
        # Load model
        try:
            model, tokenizer = check_and_load_model(model_name, device=device)
            logger.info(f"Model '{model_name}' loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            continue
        
        # Run experiment
        try:
            logs = run_experiment(
                trajectories=trajectories,
                model_name=model_name,
                model=model,
                tokenizer=tokenizer,
                classifier=classifier,
                conditions=conditions
            )
            all_experiment_logs.extend(logs)
        except Exception as e:
            logger.error(f"Experiment failed for {model_name}: {e}")
            continue
        
        # Clean up model to free memory
        del model, tokenizer
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
    
    # Write results
    if all_experiment_logs:
        output_path = Path("data/processed/experiment_logs.json")
        write_experiment_logs(all_experiment_logs, output_path)
        logger.info(f"Experiment logs written to {output_path}")
    else:
        logger.warning("No experiment logs generated")
    
    logger.info("Experiment runner completed")
    return 0

if __name__ == "__main__":
    exit(main())