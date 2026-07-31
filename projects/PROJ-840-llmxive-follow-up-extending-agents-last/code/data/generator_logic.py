"""
Generator Logic for Synthetic ALE Execution Traces (T015a).

This module defines the strict mapping rules and hardcoded constants for generating
synthetic traces. It contains the 5 "State Persistence Error" scenarios and 5
"Reasoning Deficit" scenarios.

It provides functions to generate a single trace given a seed and scenario index.
It does NOT generate the full dataset file; that is the responsibility of the
orchestrator in T015b (code/data/generator.py).
"""

import hashlib
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# Scenario Types
SCENARIO_STATE_PERSISTENCE = "state_persistence_error"
SCENARIO_REASONING_DEFICIT = "reasoning_deficit"

# --- Hardcoded Scenario Definitions ---

STATE_PERSISTENCE_SCENARIOS = [
    {
        "id": "SP01",
        "description": "Agent edits a file that was explicitly deleted in the previous step.",
        "action_pattern": "write",
        "target_state": "deleted",
        "expected_error": "FileNotFoundError: [Errno 2] No such file or directory"
    },
    {
        "id": "SP02",
        "description": "Agent attempts to read a file after moving it to a non-existent directory.",
        "action_pattern": "read",
        "target_state": "moved_to_missing",
        "expected_error": "FileNotFoundError: [Errno 2] No such file or directory"
    },
    {
        "id": "SP03",
        "description": "Agent modifies a variable that was reset to None in the previous step.",
        "action_pattern": "update_variable",
        "target_state": "null",
        "expected_error": "TypeError: 'NoneType' object is not subscriptable"
    },
    {
        "id": "SP04",
        "description": "Agent writes to a file path that was truncated to a directory in the previous step.",
        "action_pattern": "write",
        "target_state": "directory_truncation",
        "expected_error": "IsADirectoryError: [Errno 21] Is a directory"
    },
    {
        "id": "SP05",
        "description": "Agent attempts to execute a command on a process that was terminated.",
        "action_pattern": "execute",
        "target_state": "terminated",
        "expected_error": "ProcessLookupError: [Errno 3] No such process"
    }
]

REASONING_DEFICIT_SCENARIOS = [
    {
        "id": "RD01",
        "description": "Agent creates a file with the wrong extension despite instructions.",
        "action_pattern": "write",
        "target_state": "wrong_extension",
        "expected_error": "ValidationError: File extension must be .txt"
    },
    {
        "id": "RD02",
        "description": "Agent calculates a sum incorrectly in a logic block.",
        "action_pattern": "compute",
        "target_state": "incorrect_value",
        "expected_error": "AssertionError: Expected 42, got 41"
    },
    {
        "id": "RD03",
        "description": "Agent ignores a constraint to not delete specific files.",
        "action_pattern": "delete",
        "target_state": "forbidden_deletion",
        "expected_error": "ConstraintViolationError: Deletion of 'config.json' is forbidden"
    },
    {
        "id": "RD04",
        "description": "Agent fails to handle a race condition in a loop.",
        "action_pattern": "loop_update",
        "target_state": "race_condition",
        "expected_error": "KeyError: 'item_42' not found in concurrent map"
    },
    {
        "id": "RD05",
        "description": "Agent misinterprets a natural language instruction regarding order.",
        "action_pattern": "sequence",
        "target_state": "wrong_order",
        "expected_error": "SequenceError: Step 2 must precede Step 1"
    }
]

@dataclass
class StepState:
    """Represents the state of the environment after a single step."""
    step_id: int
    action: str
    target: str
    result: str
    error: Optional[str] = None
    state_hash: str = ""

@dataclass
class ExecutionTrace:
    """Represents a full execution trace for a single task."""
    trace_id: str
    scenario_type: str
    scenario_id: str
    task_description: str
    steps: List[StepState] = field(default_factory=list)
    ground_truth_label: str = ""
    seed: int = 0

def _generate_hash(content: str) -> str:
    """Generate a deterministic hash for content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def generate_task_description(scenario_type: str, scenario_id: str, seed: int) -> str:
    """
    Generates a deterministic task description based on the scenario.
    Uses the seed to introduce minor variations while keeping the core logic deterministic.
    """
    rng = random.Random(seed)
    base_templates = {
        SCENARIO_STATE_PERSISTENCE: [
            "Perform a sequence of file operations. Ensure you track the state of 'data.txt' carefully.",
            "Manage the lifecycle of 'config.json'. It may be deleted or moved unexpectedly.",
            "Execute a series of variable updates. Be aware that some variables may be reset."
        ],
        SCENARIO_REASONING_DEFICIT: [
            "Calculate the sum of a list of numbers. Precision is critical.",
            "Process a list of files in a specific order. Do not violate constraints.",
            "Execute a loop that updates a shared resource. Handle concurrency safely."
        ]
    }
    
    templates = base_templates.get(scenario_type, ["Perform general task operations."])
    base_desc = rng.choice(templates)
    
    # Add a deterministic variation based on seed
    variation_id = seed % 10
    return f"{base_desc} [Variation: {variation_id}]"

def generate_step_state(scenario: Dict[str, Any], step_idx: int, seed: int) -> StepState:
    """
    Generates a single step state based on the scenario definition.
    """
    rng = random.Random(seed + step_idx)
    
    action = scenario["action_pattern"]
    target = f"target_{scenario['id']}_{step_idx}"
    
    # Simulate the error only on the specific step that triggers the scenario
    error = None
    result = "success"
    
    # Determine if this is the trigger step (e.g., step 2 for most scenarios)
    trigger_step = 2 
    if step_idx == trigger_step:
        result = "failure"
        error = scenario["expected_error"]
    
    content = f"{action}:{target}:{result}"
    state_hash = _generate_hash(content)
    
    return StepState(
        step_id=step_idx,
        action=action,
        target=target,
        result=result,
        error=error,
        state_hash=state_hash
    )

def generate_trace(seed: int, scenario_index: int) -> ExecutionTrace:
    """
    Generates a single ExecutionTrace given a seed and a scenario index.
    
    Args:
        seed: The base seed for reproducibility.
        scenario_index: The index of the scenario to generate (0-9).
    
    Returns:
        An ExecutionTrace object.
    """
    # Determine scenario type and details
    if scenario_index < 5:
        scenario_type = SCENARIO_STATE_PERSISTENCE
        scenario = STATE_PERSISTENCE_SCENARIOS[scenario_index]
    else:
        scenario_type = SCENARIO_REASONING_DEFICIT
        scenario = REASONING_DEFICIT_SCENARIOS[scenario_index - 5]
    
    scenario_id = scenario["id"]
    
    # Generate task description
    task_description = generate_task_description(scenario_type, scenario_id, seed)
    
    # Generate steps (e.g., 5 steps per trace)
    steps = []
    for i in range(5):
        step = generate_step_state(scenario, i, seed)
        steps.append(step)
    
    # Determine ground truth label
    # In this synthetic setup, the label is derived from the scenario type
    label = "state_persistence_error" if scenario_type == SCENARIO_STATE_PERSISTENCE else "reasoning_deficit"
    
    trace_id = f"trace_{scenario_id}_{seed}"
    
    return ExecutionTrace(
        trace_id=trace_id,
        scenario_type=scenario_type,
        scenario_id=scenario_id,
        task_description=task_description,
        steps=steps,
        ground_truth_label=label,
        seed=seed
    )