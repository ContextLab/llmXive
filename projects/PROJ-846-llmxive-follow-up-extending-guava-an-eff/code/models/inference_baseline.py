"""
Baseline-Guava (Visual) Agent Inference Module

This module implements the execution of the Baseline-Guava (Visual) agent.
It attempts to load the pre-trained visual model specified in the project configuration.

CRITICAL: If the model is not found, it raises BaselineUnavailableError and halts the project.
This ensures the primary success criterion (SC-001) is always testable.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities and exceptions
# Note: Using relative imports based on the project structure provided in the API surface
try:
    from utils.config import get_path, get_hyperparameter
    from utils.exceptions import BaselineUnavailableError
    from data.models import TaskOutcome, serialize_outcome
except ImportError:
    # Fallback for direct execution or different import context
    # Adjust sys.path if running as a script
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.config import get_path, get_hyperparameter
    from utils.exceptions import BaselineUnavailableError
    from data.models import TaskOutcome, serialize_outcome

# Attempt to import deep learning dependencies
try:
    import torch
    from transformers import AutoModelForVision2Seq, AutoProcessor
    VISION_MODEL_AVAILABLE = True
except ImportError:
    VISION_MODEL_AVAILABLE = False
    print("WARNING: Transformers/Torch not installed. Visual baseline cannot run.")

class BaselineVisualAgent:
    """
    Represents the Baseline-Guava (Visual) agent.
    This agent processes raw visual inputs (frames) directly to generate actions.
    """

    def __init__(self, model_path: str, device: str = "cpu"):
        """
        Initialize the Baseline Visual Agent.
        
        Args:
            model_path: Path or HF ID for the pre-trained Guava visual model.
            device: Device to run inference on ('cpu' or 'cuda').
        
        Raises:
            BaselineUnavailableError: If the model cannot be loaded.
        """
        self.model_path = model_path
        self.device = device
        self.model = None
        self.processor = None

        if not VISION_MODEL_AVAILABLE:
            raise BaselineUnavailableError(
                f"Visual dependencies (torch, transformers) missing. "
                f"Cannot load Baseline model: {model_path}"
            )

        self._load_model()

    def _load_model(self):
        """Load the pre-trained model and processor."""
        print(f"Attempting to load Baseline-Guava Visual Model from: {self.model_path}")
        
        if not os.path.exists(self.model_path) and not self.model_path.startswith("hf://"):
            # Check if it's a local path that doesn't exist
            if not os.path.isdir(self.model_path):
                raise BaselineUnavailableError(
                    f"Baseline model path not found: {self.model_path}. "
                    f"The project requires the Baseline-Guava (Visual) agent for SC-001. "
                    f"Please configure the correct model path in code/models/config.py or download the model."
                )

        try:
            # Load processor
            self.processor = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=True)
            
            # Load model
            self.model = AutoModelForVision2Seq.from_pretrained(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                trust_remote_code=True
            )
            self.model.to(self.device)
            self.model.eval()
            
            print(f"Successfully loaded Baseline-Guava Visual Model: {self.model_path}")
            
        except Exception as e:
            raise BaselineUnavailableError(
                f"Failed to load Baseline-Guava Visual Model from {self.model_path}. "
                f"Project execution halted to ensure SC-001 testability. Error: {str(e)}"
            )

    def predict_action(self, frame_path: str, task_instruction: str) -> Dict[str, Any]:
        """
        Predict an action given a visual frame and task instruction.
        
        Args:
            frame_path: Path to the image frame.
            task_instruction: Text instruction for the task.
        
        Returns:
            Dictionary containing the predicted action and metadata.
        """
        if not VISION_MODEL_AVAILABLE:
            raise RuntimeError("Visual dependencies not available.")

        # Load image
        from PIL import Image
        image = Image.open(frame_path).convert("RGB")

        # Prepare inputs
        prompt = f"<image>\n{task_instruction}"
        inputs = self.processor(text=prompt, images=image, return_tensors="pt").to(self.device)

        # Inference
        start_time = time.time()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=50,
                do_sample=False
            )
        inference_time = time.time() - start_time

        # Decode output
        generated_text = self.processor.decode(outputs[0], skip_special_tokens=True)
        
        # Parse action (simplified parsing logic - assumes model outputs structured action)
        # In a real scenario, this would parse the specific action schema
        action = {
            "action_type": "unknown",
            "parameters": {},
            "raw_text": generated_text,
            "inference_time_ms": inference_time * 1000
        }
        
        # Basic heuristic parsing for demonstration
        if "pick" in generated_text.lower():
            action["action_type"] = "pick"
        elif "place" in generated_text.lower():
            action["action_type"] = "place"
        elif "move" in generated_text.lower():
            action["action_type"] = "move"
        
        return action

    def evaluate_trajectory(self, trajectory_frames: List[str], task_instruction: str) -> TaskOutcome:
        """
        Evaluate a full trajectory and determine the outcome.
        
        Args:
            trajectory_frames: List of paths to frames in the trajectory.
            task_instruction: The task instruction string.
        
        Returns:
            TaskOutcome object with success/failure status and metrics.
        """
        if not trajectory_frames:
            return TaskOutcome(
                success=False,
                failure_reason="Empty trajectory",
                latency_ms=0,
                steps_executed=0
            )

        total_latency = 0.0
        steps = 0
        success = True
        last_action = None

        for frame_path in trajectory_frames:
            try:
                action = self.predict_action(frame_path, task_instruction)
                total_latency += action["inference_time_ms"]
                steps += 1
                last_action = action
                
                # Simple heuristic for success (in real impl, this would check env state)
                if action["action_type"] == "unknown":
                    success = False
                    break
                    
            except Exception as e:
                success = False
                break

        return TaskOutcome(
            success=success,
            failure_reason=None if success else "Visual inference failed or invalid action",
            latency_ms=total_latency,
            steps_executed=steps,
            raw_action_log=json.dumps(last_action) if last_action else None
        )

def run_baseline_evaluation(
    dataset_path: str,
    output_path: str,
    model_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run the Baseline-Guava (Visual) agent on a held-out dataset.
    
    Args:
        dataset_path: Path to the directory containing trajectory data.
        output_path: Path to save the evaluation results.
        model_id: Override model ID/path. If None, uses config.
    
    Returns:
        List of TaskOutcome dictionaries.
    """
    # Get model path from config if not provided
    if model_id is None:
        model_id = get_hyperparameter("baseline_model_id", "guava-vision-base")
    
    # Verify model availability before starting
    # This is the critical check mandated by the task
    try:
        # Check if path exists or is a valid HF ID format
        if not os.path.exists(model_id) and not model_id.startswith("hf://") and not model_id.startswith("google/"):
            # If it looks like a local path but doesn't exist, fail immediately
            if os.path.sep in model_id or model_id.endswith("/"):
                raise BaselineUnavailableError(
                    f"Baseline model path '{model_id}' does not exist. "
                    f"Cannot proceed with evaluation. SC-001 requires the Visual Baseline."
                )
    
    except BaselineUnavailableError:
        raise

    # Initialize agent
    agent = BaselineVisualAgent(model_path=model_id)

    results = []
    trajectories = []

    # Discover trajectories (simplified logic)
    if os.path.isdir(dataset_path):
        for item in os.listdir(dataset_path):
            item_path = os.path.join(dataset_path, item)
            if os.path.isdir(item_path):
                trajectories.append(item_path)
    
    if not trajectories:
        print(f"No trajectories found in {dataset_path}")
        # Write empty results to ensure output file exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump([], f, indent=2)
        return []

    print(f"Found {len(trajectories)} trajectories to evaluate.")

    for traj_path in trajectories:
        traj_id = os.path.basename(traj_path)
        frames = []
        instruction = "default_task" # In real impl, load from metadata
        
        # Collect frames
        frame_files = sorted([f for f in os.listdir(traj_path) if f.endswith(('.png', '.jpg', '.jpeg'))])
        for f in frame_files:
            frames.append(os.path.join(traj_path, f))
        
        if frames:
            outcome = agent.evaluate_trajectory(frames, instruction)
            outcome.trajectory_id = traj_id
            results.append(serialize_outcome(outcome))
            print(f"Evaluation complete for {traj_id}: {'Success' if outcome.success else 'Failed'}")
        else:
            print(f"Warning: No frames found in {traj_id}")

    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Evaluation results saved to {output_path}")
    return results

def main():
    """Main entry point for the baseline inference script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Baseline-Guava (Visual) Inference")
    parser.add_argument("--dataset", type=str, default="data/processed/eval_held_out",
                      help="Path to evaluation dataset")
    parser.add_argument("--output", type=str, default="data/artifacts/baseline_evaluation_results.json",
                      help="Path to output results")
    parser.add_argument("--model", type=str, default=None,
                      help="Model path or ID (overrides config)")
    
    args = parser.parse_args()
    
    try:
        results = run_baseline_evaluation(
            dataset_path=args.dataset,
            output_path=args.output,
            model_id=args.model
        )
        print(f"Baseline evaluation completed. Processed {len(results)} trajectories.")
    except BaselineUnavailableError as e:
        print(f"CRITICAL ERROR: {e}")
        print("Project execution halted. The Baseline-Guava (Visual) agent is required for SC-001.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during baseline evaluation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()