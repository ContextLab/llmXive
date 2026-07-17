import json
import logging
import time
import uuid
import torch
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config import setup_logging, get_config_summary, ensure_directories
from experiments.retry_utils import retry_with_backoff, RetryError
from experiments.prompts import get_static_baseline_prompt, get_dynamic_adapter_prompt, format_prompt_for_inference
from experiments.model_loader import check_and_load_model, get_available_models, filter_models_by_memory
from models.classifier import SocioCognitiveClassifier, ClassifierConfig
from models.entities import ConflictTrajectory, SocioCognitiveState, SocioCognitiveStateType

logger = logging.getLogger(__name__)

# --- CPU-Only Verification Logic (T027) ---
def enforce_cpu_only_execution() -> None:
    """
    Verifies that the environment is CPU-only as per FR-004 and T027.
    Raises RuntimeError if GPU libraries are detected or CUDA is available.
    """
    if torch.cuda.is_available():
        # Check if any CUDA device is actually visible
        device_count = torch.cuda.device_count()
        if device_count > 0:
            raise RuntimeError(
                f"GPU execution detected: CUDA is available with {device_count} device(s). "
                "This project enforces CPU-only execution (FR-004). "
                "Please set CUDA_VISIBLE_DEVICES='' or remove GPU hardware access."
            )
    
    # Explicitly check for bitsandbytes to ensure it's not imported or used accidentally
    try:
        import bitsandbytes
        raise RuntimeError(
            "bitsandbytes library detected. This project explicitly excludes GPU-accelerated libraries "
            "and quantization tools like bitsandbytes. Please remove it from the environment."
        )
    except ImportError:
        # Expected: library should not be present
        pass

    logger.info("CPU-only execution environment verified successfully.")

# --- Classifier Loading ---
def load_classifier(config: ClassifierConfig) -> SocioCognitiveClassifier:
    """Loads the trained classifier from disk."""
    logger.info(f"Loading classifier from {config.model_path}")
    if not Path(config.model_path).exists():
        raise FileNotFoundError(
            f"Classifier model not found at {config.model_path}. "
            "Please ensure T019 and T020 have been run to generate the classifier."
        )
    return SocioCognitiveClassifier.load(config)

# --- Inference Logic ---
def run_single_turn_inference(
    model_name: str,
    prompt: str,
    max_new_tokens: int = 64,
    temperature: float = 0.7
) -> str:
    """
    Runs a single turn of inference on CPU.
    Uses retry logic for transient failures.
    """
    @retry_with_backoff(max_retries=3, base_delay=2.0)
    def _inference_call():
        model, tokenizer = check_and_load_model(model_name)
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Explicitly force CPU
        inputs = {k: v for k, v in inputs.items()} 
        # No .to('cuda') calls allowed

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True if temperature > 0 else False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response

    try:
        return _inference_call()
    except RetryError as e:
        logger.error(f"Failed to generate response for model {model_name} after retries: {e}")
        raise

# --- State Injection Fallback Logic (FR-002) ---
def get_state_for_turn(
    classifier: SocioCognitiveClassifier,
    turn_text: str,
    confidence_threshold: float = 0.6
) -> SocioCognitiveState:
    """
    Infers the socio-cognitive state from the turn text.
    Implements fallback to 'neutral monitoring' on low confidence.
    """
    prediction, confidence = classifier.predict(turn_text)
    
    if confidence < confidence_threshold:
        logger.warning(
            f"Low confidence ({confidence:.2f}) on turn text. "
            f"Falling back to neutral monitoring state (FR-002)."
        )
        return SocioCognitiveState(
            state_type=SocioCognitiveStateType.NEUTRAL_MONITORING,
            confidence=confidence,
            is_fallback=True
        )
    
    return SocioCognitiveState(
        state_type=prediction,
        confidence=confidence,
        is_fallback=False
    )

# --- Main Experiment Runner ---
def process_trajectory(
    trajectory: ConflictTrajectory,
    condition: str, # 'Adapter' or 'Static'
    model_name: str,
    classifier: SocioCognitiveClassifier,
    confidence_threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Processes a single trajectory turn-by-turn.
    Injects dynamic prompts for 'Adapter' condition based on classifier output.
    """
    logs = []
    current_context = trajectory.initial_context
    
    for turn_idx, turn in enumerate(trajectory.turns):
        # 1. Determine State (only for Adapter)
        injected_state = None
        prompt_template = None

        if condition == "Adapter":
            state = get_state_for_turn(classifier, turn.text, confidence_threshold)
            injected_state = state.state_type
            prompt_template = get_dynamic_adapter_prompt(turn.text, state)
        else:
            prompt_template = get_static_baseline_prompt(turn.text)

        # 2. Format Full Prompt
        full_prompt = format_prompt_for_inference(prompt_template, current_context)

        # 3. Run Inference
        try:
            response = run_single_turn_inference(model_name, full_prompt)
        except Exception as e:
            logger.error(f"Inference failed for trajectory {trajectory.id}, turn {turn_idx}: {e}")
            continue # Skip this turn but continue trajectory if possible

        # 4. Log Result
        log_entry = {
            "trajectory_id": str(trajectory.id),
            "turn_index": turn_idx,
            "condition": condition,
            "input_turn": turn.text,
            "injected_state": injected_state,
            "injected_state_confidence": injected_state.confidence if injected_state else None,
            "is_fallback": injected_state.is_fallback if injected_state else False,
            "model_response": response,
            "timestamp": datetime.now().isoformat()
        }
        logs.append(log_entry)

        # Update context for next turn
        current_context += f"\nUser: {turn.text}\nAssistant: {response}"
    
    return logs

def run_experiment(
    trajectories_path: Path,
    classifier_config: ClassifierConfig,
    models_to_run: List[str],
    output_path: Path,
    confidence_threshold: float = 0.6
) -> None:
    """
    Main entry point for the experiment.
    Loads trajectories, runs them through models under both conditions,
    and saves results.
    """
    # 1. Enforce CPU Only
    enforce_cpu_only_execution()

    # 2. Load Trajectories
    logger.info(f"Loading trajectories from {trajectories_path}")
    with open(trajectories_path, 'r') as f:
        raw_data = json.load(f)
    
    trajectories = [ConflictTrajectory.from_dict(item) for item in raw_data]
    logger.info(f"Loaded {len(trajectories)} trajectories.")

    # 3. Load Classifier
    classifier = load_classifier(classifier_config)

    # 4. Initialize Output
    all_logs = []

    # 5. Run Experiments
    for model_name in models_to_run:
        logger.info(f"Starting experiments for model: {model_name}")
        
        # Filter models by memory (T009 logic)
        available_models = get_available_models()
        if model_name not in available_models:
            logger.warning(f"Model {model_name} not found or exceeds memory limits. Skipping.")
            continue

        for condition in ["Adapter", "Static"]:
            logger.info(f"  Running condition: {condition}")
            for traj in trajectories:
                try:
                    logs = process_trajectory(
                        trajectory=traj,
                        condition=condition,
                        model_name=model_name,
                        classifier=classifier,
                        confidence_threshold=confidence_threshold
                    )
                    all_logs.extend(logs)
                except Exception as e:
                    logger.error(f"Error processing trajectory {traj.id} for {model_name}/{condition}: {e}")
                    continue

    # 6. Save Results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_logs, f, indent=2)
    
    logger.info(f"Experiment logs saved to {output_path}")

def main():
    """CLI entry point."""
    setup_logging()
    ensure_directories()
    
    # Configuration (simplified for T027 implementation)
    config = get_config_summary()
    
    # Paths
    trajectories_path = Path("data/processed/trajectories.json")
    classifier_config = ClassifierConfig(model_path="data/processed/classifier.pkl")
    output_path = Path("data/processed/experiment_logs.json")
    
    # Models to test (subset for safety, can be expanded)
    # Ensure these are in requirements.txt and available
    models_to_run = ["google/flan-t5-base"] # Example CPU-safe model

    run_experiment(
        trajectories_path=trajectories_path,
        classifier_config=classifier_config,
        models_to_run=models_to_run,
        output_path=output_path,
        confidence_threshold=0.6
    )

if __name__ == "__main__":
    main()