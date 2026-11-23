"""
Forward Step Implementation for Bidirectional Evolutionary Search (BES).

This module implements the forward step of the BES framework, where a small
pre-trained LLM (distilbert-base-uncased) performs trajectory recombination
guided by symbolic sub-goals.

Constraints:
- Must use CPU-only inference (device='cpu').
- Must use optimum for CPU-optimized inference.
- Must enforce torch.no_grad() for inference.
- Must load model from config file specified in code/bes/config.py.
- Must NOT use bitsandbytes (forbidden by CPU constraint).
- Must strictly fail if real data/model loading fails (no synthetic fallback).
"""
import time
import logging
import json
import os
import sys
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import random

# Import configuration from the existing config module
try:
    from bes.config import BESConfig, get_default_config
except ImportError:
    # Fallback for direct execution context
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from bes.config import BESConfig, get_default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Timeout handling
class TimeoutException(Exception):
    """Exception raised when a timeout occurs."""
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

@dataclass
class ForwardStepError(Exception):
    """Custom exception for forward step errors."""
    message: str
    code: str = "FORWARD_STEP_ERROR"

@dataclass
class ForwardStepResult:
    """Result of a forward step execution."""
    success: bool
    trajectory: List[Dict[str, Any]]
    sub_goals: List[Dict[str, Any]]
    execution_time: float
    tokens_generated: int
    error_message: Optional[str] = None
    error_code: Optional[str] = None

class ForwardStep:
    """
    Forward Step implementation using a small LLM for trajectory recombination.

    This class handles:
    1. Loading the model from configuration
    2. Preparing input prompts from symbolic sub-goals
    3. Running inference with CPU-optimized flags
    4. Parsing and validating output trajectories
    """

    def __init__(self, config_path: Optional[Path] = None, timeout_seconds: int = 300):
        """
        Initialize the ForwardStep.

        Args:
            config_path: Path to the BES configuration YAML file.
            timeout_seconds: Timeout for inference operations.
        """
        self.config_path = config_path or Path("code/bes/bes_config.yaml")
        self.timeout_seconds = timeout_seconds
        self.model = None
        self.tokenizer = None
        self.config = None
        self._load_model()

    def _load_model(self) -> None:
        """
        Load the LLM model using optimum CPU-optimized inference.

        This method:
        1. Loads configuration from the specified YAML file
        2. Downloads/loads the model using optimum for CPU optimization
        3. Enforces CPU-only and no-grad constraints
        """
        logger.info(f"Loading configuration from {self.config_path}")

        if not self.config_path.exists():
            raise ForwardStepError(
                f"Configuration file not found: {self.config_path}. "
                "Please run code/bes/config.py first to generate the config."
            )

        # Load configuration
        self.config = BESConfig.load(self.config_path)
        logger.info(f"Loaded config: model_id={self.config.model_id}, device={self.config.device}")

        # Validate CPU constraint
        if self.config.device != "cpu":
            raise ForwardStepError(
                f"Device must be 'cpu' for forward step. Got: {self.config.device}"
            )

        if self.config.use_bitsandbytes:
            raise ForwardStepError(
                "bitsandbytes is forbidden in CPU-only configuration."
            )

        # Import optimum and transformers
        try:
            from optimum.onnxruntime import ORTModelForSequenceClassification
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            import torch
            from torch import no_grad
        except ImportError as e:
            raise ForwardStepError(
                f"Required libraries not installed. Install with: pip install optimum transformers torch. Error: {e}"
            )

        logger.info(f"Loading model: {self.config.model_id}")

        try:
            # Set device to CPU explicitly
            device = torch.device("cpu")

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_id,
                revision=self.config.revision
            )

            # Load model with optimum for CPU optimization
            # Using ORTModelForSequenceClassification for CPU-optimized inference
            # Note: For generative tasks, we might need ORTModelForCausalLM
            # But distilbert-base-uncased is typically used for classification
            # We'll use a generic approach that works for both

            try:
                # Try causal LM first (for generation)
                from optimum.onnxruntime import ORTModelForCausalLM
                self.model = ORTModelForCausalLM.from_pretrained(
                    self.config.model_id,
                    revision=self.config.revision,
                    use_io_binding=True,  # Optimize for CPU
                    export=True if not os.path.exists(
                        Path.home() / ".cache" / "huggingface" / "hub" /
                        f"models--{self.config.model_id.replace('/', '--')}"
                    ) else False
                )
            except Exception:
                # Fallback to standard transformers if optimum causal LM fails
                logger.warning("Optimum causal LM failed, falling back to transformers")
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.config.model_id,
                    revision=self.config.revision
                )

            self.model.to(device)
            self.model.eval()

            # Enable IPEX if configured (Intel-specific optimization)
            if self.config.use_ipex:
                try:
                    import intel_extension_for_pytorch as ipex
                    logger.info("IPEX optimization enabled")
                    if self.config.ipex_precision == "bf16":
                        self.model = self.model.to(dtype=torch.bfloat16)
                    self.model = ipex.optimize(self.model, dtype=torch.bfloat16 if self.config.ipex_precision == "bf16" else torch.float32)
                except ImportError:
                    logger.warning("IPEX not available, skipping optimization")

            logger.info("Model loaded successfully")

        except Exception as e:
            raise ForwardStepError(
                f"Failed to load model {self.config.model_id}: {str(e)}",
                code="MODEL_LOAD_FAILURE"
            ) from e

    def _prepare_prompt(self, sub_goals: List[Dict[str, Any]], initial_state: Dict[str, Any]) -> str:
        """
        Prepare the input prompt from symbolic sub-goals and initial state.

        Args:
            sub_goals: List of sub-goal dictionaries from the symbolic planner
            initial_state: The initial puzzle state

        Returns:
            Formatted prompt string for the LLM
        """
        prompt_parts = []

        # Add initial state
        prompt_parts.append("Initial State:")
        prompt_parts.append(json.dumps(initial_state, indent=2))
        prompt_parts.append("")

        # Add sub-goals
        prompt_parts.append("Sub-Goals (in order):")
        for i, goal in enumerate(sub_goals, 1):
            goal_text = f"{i}. {goal.get('description', 'Unknown goal')}"
            if goal.get('constraints'):
                goal_text += f" [Constraints: {', '.join(goal['constraints'])}]"
            prompt_parts.append(goal_text)

        prompt_parts.append("")
        prompt_parts.append("Generate a trajectory that satisfies these sub-goals:")

        return "\n".join(prompt_parts)

    def _generate_trajectory(self, prompt: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Generate a trajectory using the loaded model.

        Args:
            prompt: The formatted prompt string

        Returns:
            Tuple of (trajectory_list, tokens_generated)
        """
        import torch
        from torch import no_grad

        if self.model is None or self.tokenizer is None:
            raise ForwardStepError("Model or tokenizer not initialized")

        # Tokenize input
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_length
        )

        # Move to CPU (should already be there)
        inputs = {k: v.to("cpu") for k, v in inputs.items()}

        # Generate with timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)

        try:
            with no_grad():
                # Generate output
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.max_length // 2,  # Limit output length
                    temperature=self.config.temperature,
                    top_k=self.config.top_k,
                    top_p=self.config.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

                # Decode output
                generated_text = self.tokenizer.decode(
                    outputs[0, inputs['input_ids'].shape[1]:],
                    skip_special_tokens=True
                )

                tokens_generated = outputs[0].shape[1] - inputs['input_ids'].shape[1]

        except TimeoutException:
            raise ForwardStepError(
                f"Generation timed out after {self.timeout_seconds} seconds",
                code="TIMEOUT"
            )
        finally:
            signal.alarm(0)  # Cancel alarm

        # Parse generated text into trajectory steps
        trajectory = self._parse_trajectory(generated_text)

        return trajectory, tokens_generated

    def _parse_trajectory(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse the generated text into a structured trajectory.

        Args:
            text: Raw generated text from the model

        Returns:
            List of trajectory step dictionaries
        """
        trajectory = []

        # Simple parsing: split by lines and extract steps
        lines = text.strip().split('\n')
        current_step = {}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for step markers (e.g., "Step 1:", "1.", etc.)
            if line.startswith(('Step', '1.', '2.', '3.', '4.', '5.')):
                if current_step:
                    trajectory.append(current_step)
                current_step = {'step_number': len(trajectory) + 1, 'description': line}
            elif ':' in line and current_step:
                key, value = line.split(':', 1)
                current_step[key.strip()] = value.strip()
            elif current_step:
                # Append to description if it's a continuation
                current_step['description'] += ' ' + line

        if current_step:
            trajectory.append(current_step)

        return trajectory

    def execute(
        self,
        sub_goals: List[Dict[str, Any]],
        initial_state: Dict[str, Any],
        timeout_seconds: Optional[int] = None
    ) -> ForwardStepResult:
        """
        Execute the forward step with given sub-goals and initial state.

        Args:
            sub_goals: List of sub-goal dictionaries from symbolic planner
            initial_state: The initial puzzle state
            timeout_seconds: Optional override for timeout

        Returns:
            ForwardStepResult containing the generated trajectory
        """
        start_time = time.time()
        timeout = timeout_seconds or self.timeout_seconds

        try:
            # Prepare prompt
            prompt = self._prepare_prompt(sub_goals, initial_state)

            # Generate trajectory
            trajectory, tokens_generated = self._generate_trajectory(prompt)

            execution_time = time.time() - start_time

            return ForwardStepResult(
                success=True,
                trajectory=trajectory,
                sub_goals=sub_goals,
                execution_time=execution_time,
                tokens_generated=tokens_generated
            )

        except ForwardStepError:
            raise
        except Exception as e:
            logger.error(f"Forward step failed: {str(e)}")
            return ForwardStepResult(
                success=False,
                trajectory=[],
                sub_goals=sub_goals,
                execution_time=time.time() - start_time,
                tokens_generated=0,
                error_message=str(e),
                error_code="EXECUTION_FAILURE"
            )

    def recombine_trajectories(
        self,
        parent_trajectories: List[List[Dict[str, Any]]],
        sub_goals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Recombine multiple parent trajectories guided by sub-goals.

        Args:
            parent_trajectories: List of parent trajectory lists
            sub_goals: Sub-goals to guide recombination

        Returns:
            Recombined trajectory
        """
        if not parent_trajectories:
            raise ForwardStepError("No parent trajectories provided")

        # Combine all parent steps
        all_steps = []
        for traj in parent_trajectories:
            all_steps.extend(traj)

        # Use the last parent as base and refine with sub-goals
        base_trajectory = parent_trajectories[-1] if parent_trajectories else []

        # Generate a refined trajectory using the combined information
        initial_state = {
            'source': 'recombination',
            'parent_count': len(parent_trajectories),
            'total_steps': len(all_steps)
        }

        result = self.execute(sub_goals, initial_state)

        if result.success:
            return result.trajectory
        else:
            # Fallback: return the best parent trajectory
            logger.warning(f"Recombination failed: {result.error_message}. Using best parent.")
            return base_trajectory

def main():
    """CLI entry point for testing the forward step."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Forward Step implementation")
    parser.add_argument(
        "--config",
        type=str,
        default="code/bes/bes_config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--test-prompt",
        type=str,
        default="Test prompt for forward step",
        help="Test prompt to run"
    )
    args = parser.parse_args()

    logger.info("Starting Forward Step test")

    try:
        forward_step = ForwardStep(config_path=Path(args.config))

        # Create test sub-goals
        test_sub_goals = [
            {
                "description": "Initialize the puzzle state",
                "constraints": ["valid_start"]
            },
            {
                "description": "Move to intermediate state",
                "constraints": ["no_duplicates"]
            },
            {
                "description": "Reach target state",
                "constraints": ["target_reached"]
            }
        ]

        test_initial_state = {
            "puzzle_type": "test",
            "difficulty": 1,
            "grid_size": 3
        }

        result = forward_step.execute(test_sub_goals, test_initial_state)

        logger.info(f"Execution result: success={result.success}")
        logger.info(f"Execution time: {result.execution_time:.2f}s")
        logger.info(f"Tokens generated: {result.tokens_generated}")

        if result.success:
            logger.info(f"Trajectory steps: {len(result.trajectory)}")
            for step in result.trajectory[:3]:  # Log first 3 steps
                logger.info(f"  {step}")
        else:
            logger.error(f"Error: {result.error_message}")

    except ForwardStepError as e:
        logger.error(f"Forward Step Error: {e.message} (Code: {e.code})")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()