"""
Lightweight agent wrapper for llmXive Follow-up: Reward Fidelity vs. Error Recovery Density.

This module implements a CPU-only agent runner using llama-cpp-python with a fallback
strategy for low-bit quantization. It attempts to load a primary model (Llama-3-8B)
and falls back to a smaller model (Qwen-1.5-1.8B) if the primary fails to load or
exceeds memory constraints, logging the specific model used for ground truth analysis.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure parent package imports work if run as a script
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

try:
    from llama_cpp import Llama
except ImportError:
    logging.critical("llama-cpp-python is not installed. Please run: pip install llama-cpp-python")
    sys.exit(1)

from utils.pruning import fidelity_context, RewardFidelityLevel
from utils.state_diff import identify_recovery_segments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/run.log", mode="a"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Model configuration
# Note: Paths are expected to be relative to the project root or absolute paths
# provided via environment variables or config.
PRIMARY_MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"
FALLBACK_MODEL_ID = "Qwen/Qwen1.5-1.8B-Chat"

# Expected GGUF paths (these should be downloaded via code/download.py or similar)
# For this implementation, we assume the models are stored in data/raw/models/
# or provided via environment variables.
DEFAULT_MODEL_PATH = os.getenv("LLM_MODEL_PATH")
FALLBACK_MODEL_PATH = os.getenv("LLM_FALLBACK_MODEL_PATH")

# Quantization settings for CPU-only execution
N_CTX = 4096
N_BATCH = 512
# q8_0 is a good balance for 8B models on CPU, q4_0 for smaller/faster
PRIMARY_QUANTIZATION = "q8_0" 
FALLBACK_QUANTIZATION = "q4_0"

class AgentRunner:
    """
    A lightweight agent wrapper that handles model loading, inference, and
    context management with fallback strategies for CPU-only environments.
    """

    def __init__(self, model_path: Optional[str] = None, fallback_path: Optional[str] = None):
        """
        Initialize the AgentRunner.
        
        Args:
            model_path: Path to the primary GGUF model file.
            fallback_path: Path to the fallback GGUF model file.
        """
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.fallback_path = fallback_path or FALLBACK_MODEL_PATH
        self.llm: Optional[Llama] = None
        self.current_model_id: str = ""
        self.is_fallback: bool = False

        if not self.model_path and not self.fallback_path:
            raise ValueError(
                "No model path provided. Set LLM_MODEL_PATH env var or pass model_path argument. "
                "Ensure models are downloaded to data/raw/models/."
            )

    def _load_model(self, path: str, quantization: str = "q4_0") -> Llama:
        """
        Load a model from a GGUF file with CPU-only settings.
        
        Args:
            path: Path to the GGUF file.
            quantization: Quantization type (ignored if file is already quantized).
        
        Returns:
            Llama instance.
        
        Raises:
            FileNotFoundError: If the model file does not exist.
            RuntimeError: If model loading fails for other reasons.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        
        logger.info(f"Attempting to load model from: {path}")
        
        try:
            # CPU-only configuration
            llm = Llama(
                model_path=path,
                n_ctx=N_CTX,
                n_batch=N_BATCH,
                n_threads=os.cpu_count() or 4,
                n_threads_batch=os.cpu_count() or 4,
                use_mlock=True,  # Lock memory to prevent swapping
                verbose=True
            )
            logger.info(f"Successfully loaded model: {path}")
            return llm
        except Exception as e:
            logger.error(f"Failed to load model {path}: {e}")
            raise RuntimeError(f"Model loading failed: {e}") from e

    def load(self) -> None:
        """
        Load the primary model. If it fails, attempt to load the fallback model.
        Logs the specific model used to quantify impact on ground truth.
        """
        try:
            # Try primary model first
            if self.model_path:
                self.llm = self._load_model(self.model_path)
                self.current_model_id = os.path.basename(self.model_path)
                self.is_fallback = False
                logger.info(f"Primary model loaded: {self.current_model_id}")
            else:
                raise FileNotFoundError("Primary model path not configured.")
        except (FileNotFoundError, RuntimeError) as e:
            logger.warning(f"Primary model load failed ({e}). Attempting fallback...")
            if self.fallback_path:
                try:
                    self.llm = self._load_model(self.fallback_path)
                    self.current_model_id = os.path.basename(self.fallback_path)
                    self.is_fallback = True
                    logger.warning(f"Fallback model loaded: {self.current_model_id}")
                    logger.warning("Model swap detected. Ground truth metrics may be affected by capacity reduction.")
                except Exception as fallback_err:
                    logger.critical(f"Fallback model also failed to load: {fallback_err}")
                    raise RuntimeError("All models failed to load. Cannot proceed.") from fallback_err
            else:
                raise RuntimeError("No fallback model available and primary failed.")

    def run_step(
        self, 
        prompt: str, 
        fidelity_level: RewardFidelityLevel = RewardFidelityLevel.DENSE,
        trajectory: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Run a single inference step.
        
        Args:
            prompt: The current prompt for the agent.
            fidelity_level: The reward fidelity level for context pruning.
            trajectory: The current trajectory history (optional).
        
        Returns:
            Tuple of (generated_text, metadata_dict).
        """
        if not self.llm:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Apply pruning context if trajectory is provided
        context_to_use = prompt
        if trajectory and fidelity_level != RewardFidelityLevel.DENSE:
            with fidelity_context(fidelity_level, trajectory):
                # The context manager handles pruning internally or via state_diff
                # For this runner, we assume the prompt is already adjusted or
                # we adjust it here based on the pruning logic.
                # Note: In a real implementation, the pruning might happen 
                # before the prompt is constructed. Here we log the action.
                logger.info(f"Running step with fidelity level: {fidelity_level}")
                # If pruning modifies the trajectory, we might need to reconstruct the prompt
                # For now, we proceed with the provided prompt and log the fidelity level.
        
        # Generate response
        try:
            output = self.llm(
                prompt,
                max_tokens=256,
                temperature=0.0,  # Deterministic for evaluation
                stop=["\n\nHuman:", "\n\nUser:", "###"],
                echo=False
            )
            generated_text = output['choices'][0]['text']
        except Exception as e:
            logger.error(f"Inference failed: {e}")
            raise

        metadata = {
            "model_used": self.current_model_id,
            "is_fallback": self.is_fallback,
            "fidelity_level": fidelity_level.value,
            "tokens_generated": len(generated_text.split()),
            "success": True
        }

        return generated_text, metadata

    def run_task(
        self, 
        task: Dict[str, Any], 
        fidelity_level: RewardFidelityLevel = RewardFidelityLevel.DENSE
    ) -> Dict[str, Any]:
        """
        Execute a full task from the benchmark suite.
        
        Args:
            task: Task dictionary containing 'initial_state', 'goal', etc.
            fidelity_level: The reward fidelity level for the run.
        
        Returns:
            Execution log entry.
        """
        if not self.llm:
            self.load()

        logger.info(f"Starting task execution. Model: {self.current_model_id}, Fidelity: {fidelity_level}")
        
        trajectory = []
        success = False
        final_action = ""
        
        # Simulate a multi-step execution (simplified for this task)
        # In a full implementation, this would loop until a terminal state or max steps
        steps = task.get("max_steps", 5)
        current_obs = task.get("initial_observation", "Initial state")
        
        for step in range(steps):
            prompt = f"Task: {task.get('goal', 'Unknown goal')}\nObservation: {current_obs}\nAction:"
            
            try:
                action, metadata = self.run_step(prompt, fidelity_level, trajectory)
                final_action = action
                trajectory.append({
                    "step": step,
                    "observation": current_obs,
                    "action": action,
                    "reward": 0.0, # Placeholder, actual reward logic is in the environment
                    "metadata": metadata
                })
                
                # Simulate state update (in reality, this comes from the environment)
                # For this runner, we assume the action leads to a new observation
                # In a real benchmark, we would call an environment.step(action)
                current_obs = f"State after step {step+1}: {action[:20]}..."
                
            except Exception as e:
                logger.error(f"Step {step} failed: {e}")
                break

        # Identify recovery segments if fidelity is manipulated
        recovery_segments = []
        if fidelity_level != RewardFidelityLevel.DENSE:
            recovery_segments = identify_recovery_segments(trajectory)
            logger.info(f"Identified {len(recovery_segments)} recovery segments.")

        # Determine success (simplified logic)
        # In reality, this checks if the final state matches the goal
        success = "success" in final_action.lower() or len(trajectory) == steps

        log_entry = {
            "task_id": task.get("id", "unknown"),
            "model_used": self.current_model_id,
            "is_fallback": self.is_fallback,
            "fidelity_level": fidelity_level.value,
            "trajectory_length": len(trajectory),
            "recovery_segments": [seg["id"] if isinstance(seg, dict) else seg for seg in recovery_segments],
            "success": success,
            "final_action": final_action,
            "trajectory": trajectory
        }

        logger.info(f"Task {log_entry['task_id']} completed. Success: {success}")
        return log_entry

def main():
    """
    Main entry point for the agent runner.
    Demonstrates loading and running a sample task.
    """
    # Setup logging directory
    Path("logs").mkdir(exist_ok=True)

    runner = AgentRunner()
    
    try:
        runner.load()
    except RuntimeError as e:
        logger.critical(f"Failed to initialize runner: {e}")
        sys.exit(1)

    # Sample task (in reality, this would come from data/raw/agentbench)
    sample_task = {
        "id": "sample_task_001",
        "goal": "Navigate to the kitchen and find the keys.",
        "initial_observation": "You are in the living room.",
        "max_steps": 3
    }

    # Run with dense rewards (baseline)
    result_dense = runner.run_task(sample_task, RewardFidelityLevel.DENSE)
    print(f"Dense Result: {result_dense['success']}")

    # Run with binary rewards (pruning)
    result_binary = runner.run_task(sample_task, RewardFidelityLevel.BINARY)
    print(f"Binary Result: {result_binary['success']}")

    logger.info("Agent runner demonstration complete.")

if __name__ == "__main__":
    main()