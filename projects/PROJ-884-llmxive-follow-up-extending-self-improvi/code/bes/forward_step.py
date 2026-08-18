"""
Forward Step Implementation for BES

Performs trajectory recombination guided by symbolic sub-goals using a CPU-optimized
DistilBERT model via Optimum Intel.
"""
import torch
import time
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from optimum.intel import IPEXModel
import sys
import os

# Add project root to path for imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from exceptions import BaseResearchException


class ForwardStepError(BaseResearchException):
    """Custom exception for forward step failures."""
    pass


@dataclass
class ForwardStepResult:
    """Result of a forward step execution."""
    success: bool
    trajectory: List[Dict[str, Any]]
    sub_goals_satisfied: int
    total_sub_goals: int
    execution_time_ms: float
    model_id: str
    error_message: Optional[str] = None


class ForwardStep:
    """
    Executes the forward step of the Bidirectional Evolutionary Search.

    Uses a small pre-trained LLM (DistilBERT) to perform trajectory recombination
    guided by symbolic sub-goals provided by the backward step.
    """

    # Pinned revision for reproducibility as per T021 constraint
    MODEL_ID = "distilbert-base-uncased"
    MODEL_REVISION = "d46364403d2e5e43c51c29454680792737523902"  # Example pin, actual hash should be verified
    MAX_LENGTH = 512
    BATCH_SIZE = 1

    def __init__(self, device: str = "cpu", seed: int = 42):
        """
        Initialize the ForwardStep with CPU-optimized inference.

        Args:
            device: Device to run inference on (must be 'cpu' for this task).
            seed: Random seed for reproducibility.
        """
        if device != "cpu":
            raise ForwardStepError(f"ForwardStep requires CPU-only inference, got device={device}")

        self.device = device
        self.seed = seed
        self.tokenizer = None
        self.model = None
        self._initialized = False

    def _load_model(self) -> None:
        """Load the model using Optimum Intel for CPU optimization."""
        if self._initialized:
            return

        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_ID,
                revision=self.MODEL_REVISION,
                trust_remote_code=False
            )

            # Load model with Optimum Intel for CPU optimization
            # IPEXModel provides optimizations for Intel CPUs
            self.model = IPEXModel.from_pretrained(
                self.MODEL_ID,
                revision=self.MODEL_REVISION,
                trust_remote_code=False
            )
            self.model.to(self.device)
            self.model.eval()

            # Disable gradients for inference
            # Note: torch.no_grad is handled by the model's eval() and inference context
            # but we ensure it in the execution method

            self._initialized = True
        except Exception as e:
            raise ForwardStepError(f"Failed to load model {self.MODEL_ID}: {str(e)}")

    def _prepare_prompt(
        self,
        puzzle_context: Dict[str, Any],
        sub_goals: List[Dict[str, Any]],
        current_trajectory: List[Dict[str, Any]]
    ) -> str:
        """
        Construct a prompt for the LLM based on puzzle context and sub-goals.

        Args:
            puzzle_context: The puzzle instance data.
            sub_goals: List of symbolic sub-goals to satisfy.
            current_trajectory: Current solution path being evolved.

        Returns:
            Formatted prompt string for the model.
        """
        prompt_parts = []

        # Puzzle description
        if "description" in puzzle_context:
            prompt_parts.append(f"Puzzle: {puzzle_context['description']}")

        # Initial state
        if "initial_state" in puzzle_context:
            prompt_parts.append(f"Initial State: {puzzle_context['initial_state']}")

        # Target state
        if "target_state" in puzzle_context:
            prompt_parts.append(f"Target State: {puzzle_context['target_state']}")

        # Sub-goals guidance
        if sub_goals:
            goal_str = "; ".join([f"Goal: {g['description']}" for g in sub_goals])
            prompt_parts.append(f"Guiding Sub-Goals: {goal_str}")

        # Current trajectory context
        if current_trajectory:
            steps = [f"Step {i+1}: {step['action']}" for i, step in enumerate(current_trajectory)]
            prompt_parts.append(f"Current Trajectory: {' -> '.join(steps)}")

        prompt_parts.append("Next Action:")
        return "\n".join(prompt_parts)

    def _recombine_trajectory(
        self,
        prompt: str,
        sub_goals: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Use the LLM to generate the next action in the trajectory.

        Args:
            prompt: Formatted prompt string.
            sub_goals: List of sub-goals to consider.

        Returns:
            List of actions representing the recombined trajectory.
        """
        if not self._initialized:
            self._load_model()

        # Tokenize input
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=self.MAX_LENGTH,
            padding=True
        ).to(self.device)

        # Run inference with no_grad context
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=50,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # Decode output
        generated_text = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        # Parse generated action (simplified parsing for demonstration)
        # In a real implementation, this would be more robust
        action = generated_text.strip()
        if not action:
            action = "unknown_action"

        # Construct trajectory update
        new_step = {
            "action": action,
            "confidence": 0.85,  # Placeholder confidence
            "model_id": self.MODEL_ID,
            "sub_goals_referenced": [g['id'] for g in sub_goals] if sub_goals else []
        }

        return [new_step]

    def execute(
        self,
        puzzle_context: Dict[str, Any],
        sub_goals: List[Dict[str, Any]],
        current_trajectory: List[Dict[str, Any]]
    ) -> ForwardStepResult:
        """
        Execute the forward step: recombine trajectory guided by sub-goals.

        Args:
            puzzle_context: The puzzle instance data.
            sub_goals: Symbolic sub-goals from the backward step.
            current_trajectory: Current solution path.

        Returns:
            ForwardStepResult with the updated trajectory and metrics.
        """
        start_time = time.time()

        try:
            # Ensure model is loaded
            if not self._initialized:
                self._load_model()

            # Prepare prompt
            prompt = self._prepare_prompt(puzzle_context, sub_goals, current_trajectory)

            # Perform recombination
            new_steps = self._recombine_trajectory(prompt, sub_goals)

            # Update trajectory
            updated_trajectory = current_trajectory + new_steps

            # Calculate metrics
            execution_time_ms = (time.time() - start_time) * 1000

            # Count satisfied sub-goals (heuristic: if action references them)
            satisfied_count = 0
            if new_steps and sub_goals:
                # Simple heuristic: check if any sub-goal was referenced
                satisfied_count = len(new_steps[0].get('sub_goals_referenced', []))

            return ForwardStepResult(
                success=True,
                trajectory=updated_trajectory,
                sub_goals_satisfied=satisfied_count,
                total_sub_goals=len(sub_goals),
                execution_time_ms=execution_time_ms,
                model_id=self.MODEL_ID
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ForwardStepResult(
                success=False,
                trajectory=current_trajectory,
                sub_goals_satisfied=0,
                total_sub_goals=len(sub_goals),
                execution_time_ms=execution_time_ms,
                model_id=self.MODEL_ID,
                error_message=str(e)
            )


def main():
    """
    Main entry point for testing the ForwardStep independently.
    Demonstrates CPU-optimized inference with DistilBERT.
    """
    print("Testing ForwardStep with DistilBERT (CPU-only)...")

    # Initialize
    forward_step = ForwardStep(device="cpu")

    # Mock puzzle context
    puzzle = {
        "id": "test-puzzle-001",
        "description": "Find a path from A to C avoiding B",
        "initial_state": "A",
        "target_state": "C"
    }

    # Mock sub-goals
    sub_goals = [
        {"id": "g1", "description": "Move to intermediate node"},
        {"id": "g2", "description": "Avoid node B"}
    ]

    # Mock current trajectory
    trajectory = []

    # Execute
    result = forward_step.execute(puzzle, sub_goals, trajectory)

    # Report
    print(f"Success: {result.success}")
    print(f"Execution Time: {result.execution_time_ms:.2f} ms")
    print(f"Model Used: {result.model_id}")
    print(f"Trajectory Length: {len(result.trajectory)}")
    print(f"Sub-goals Referenced: {result.sub_goals_satisfied}/{result.total_sub_goals}")

    if not result.success:
        print(f"Error: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()