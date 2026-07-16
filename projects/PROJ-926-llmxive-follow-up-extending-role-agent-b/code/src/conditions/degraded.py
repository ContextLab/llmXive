"""
Degraded World Model Condition Implementation.

Configures the WIA (World Model Inference Agent) prediction horizon to 0,
effectively removing predictive context from the agent's prompt.
This simulates a 'Degraded' cognitive state where the agent acts without
future-state anticipation.
"""

import os
import json
from typing import Any, Dict, Optional

# Import existing configuration
from src.config.config import SEED, DATA_PATH, MODEL_ID

# Import existing stream utilities
from src.data.stream_utils import load_trajectory_dataset


class DegradedConfig:
    """Configuration container for the Degraded World Model condition."""

    def __init__(self, horizon: int = 0, randomized_prompt: bool = True):
        """
        Initialize the degraded configuration.

        Args:
            horizon: The WIA prediction horizon. Set to 0 for Degraded condition.
            randomized_prompt: If True, randomizes specific prompt elements to
                               ensure no predictive context leaks through.
        """
        self.horizon = horizon
        self.randomized_prompt = randomized_prompt
        self.condition_name = "degraded"

    def __repr__(self) -> str:
        return f"DegradedConfig(horizon={self.horizon}, randomized_prompt={self.randomized_prompt})"


def get_degraded_prompt_template() -> str:
    """
    Returns a prompt template that explicitly lacks predictive context.

    This template is used when horizon=0 to ensure the agent cannot
    simulate future states.
    """
    return (
        "You are an agent in the ALFWorld environment.\n"
        "TASK: {task_description}\n"
        "CURRENT STATE: {current_state}\n"
        "HISTORY: {action_history}\n\n"
        "INSTRUCTIONS:\n"
        "1. Analyze the current state only. Do not simulate or predict future states.\n"
        "2. Select the immediate next action required to progress.\n"
        "3. Output ONLY the action command.\n"
        "Note: Prediction horizon is set to 0. No future planning is allowed.\n"
    )


def verify_output_no_predictive_context(output_text: str) -> bool:
    """
    Verifies that the generated output does not contain predictive context.

    Checks for common phrases that indicate future simulation or planning
    which should be absent in the Degraded condition.

    Args:
        output_text: The raw text output from the agent.

    Returns:
        True if no predictive context is detected, False otherwise.
    """
    predictive_keywords = [
        "will", "going to", "predict", "simulate", "future",
        "anticipate", "plan", "next step after", "then I will"
    ]

    lower_text = output_text.lower()
    for keyword in predictive_keywords:
        if keyword in lower_text:
            return False

    return True


def configure_degraded_environment(task_definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configures a task definition for the degraded condition.

    Modifies the task definition to enforce horizon=0 constraints.

    Args:
        task_definition: The original task definition from the task bank.

    Returns:
        A modified task definition ready for degraded execution.
    """
    config = DegradedConfig(horizon=0)

    modified_def = task_definition.copy()
    modified_def["condition"] = config.condition_name
    modified_def["wia_horizon"] = config.horizon
    modified_def["prompt_template"] = get_degraded_prompt_template()
    modified_def["validation_fn"] = verify_output_no_predictive_context

    return modified_def


def run_degraded_condition_check(trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a validation check on a trajectory to ensure it adheres to degraded constraints.

    Args:
        trajectory_data: A dictionary containing the trajectory actions and states.

    Returns:
        A dictionary with validation results and metadata.
    """
    config = DegradedConfig(horizon=0)
    results = {
        "condition": config.condition_name,
        "horizon": config.horizon,
        "valid": True,
        "issues": []
    }

    # Check if the trajectory data contains any predictive fields
    if "future_predictions" in trajectory_data or "simulated_states" in trajectory_data:
        results["valid"] = False
        results["issues"].append("Trajectory contains predictive context fields")

    # Check action descriptions for predictive language
    actions = trajectory_data.get("actions", [])
    for i, action in enumerate(actions):
        if not verify_output_no_predictive_context(str(action)):
            results["valid"] = False
            results["issues"].append(f"Action {i} contains predictive language")

    return results


def load_and_verify_degraded_data(data_path: str) -> None:
    """
    Loads data from the specified path and verifies it meets degraded condition criteria.

    Args:
        data_path: Path to the JSON file containing trajectory data.

    Raises:
        ValueError: If the data does not meet degraded condition criteria.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(data_path, 'r') as f:
        data = json.load(f)

    # Verify at least one entry exists
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Data file is empty or not a list of trajectories")

    # Verify each entry has the degraded condition marker
    for i, entry in enumerate(data):
        if entry.get("condition") != "degraded":
            raise ValueError(f"Entry {i} is not marked as 'degraded' condition")
        if entry.get("wia_horizon") != 0:
            raise ValueError(f"Entry {i} does not have wia_horizon=0")

    print(f"Successfully verified {len(data)} degraded trajectories in {data_path}")


def run():
    """
    Entry point for the degraded condition module.
    Demonstrates configuration and verification logic.
    """
    print("Initializing Degraded World Model Condition...")
    config = DegradedConfig(horizon=0)
    print(f"Configuration: {config}")

    # Example task definition
    example_task = {
        "task_id": "test_001",
        "description": "pick up the apple",
        "initial_state": "You are in a kitchen."
    }

    modified_task = configure_degraded_environment(example_task)
    print(f"Modified Task: {json.dumps(modified_task, indent=2)}")

    # Example validation
    test_trajectory = {
        "actions": ["go to table", "pick up apple"],
        "states": ["kitchen", "table"]
    }
    validation_result = run_degraded_condition_check(test_trajectory)
    print(f"Validation Result: {json.dumps(validation_result, indent=2)}")

    print("Degraded condition module initialized successfully.")


if __name__ == "__main__":
    run()