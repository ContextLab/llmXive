"""
Logic for generating ALE Execution Traces.

This module defines the strict mapping rules and data structures for
generating synthetic traces representing "State Persistence Error" and
"Reasoning Deficit" scenarios.
"""
import hashlib
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class StepState:
    """Represents the state of the environment at a specific step."""
    step_id: int
    action: str
    target: str
    result: str
    error: Optional[str] = None

@dataclass
class ExecutionTrace:
    """Represents a full execution trace."""
    task_id: str
    task_description: str
    steps: List[StepState]
    final_state: Dict[str, Any]
    ground_truth: str

def generate_task_description(scenario_type: str, scenario_description: str, seed: int) -> str:
    """
    Generate a deterministic task description based on the scenario.
    """
    random.seed(seed)
    # Base template
    templates = {
        "State Persistence Error": "Perform the following sequence of operations. Note the state changes carefully.",
        "Reasoning Deficit": "Solve the following logic puzzle. Pay attention to the order of operations."
    }
    base = templates.get(scenario_type, "Perform the task.")
    # Add a deterministic random suffix to make it unique per seed
    suffix = f" [Context ID: {hashlib.sha256(str(seed).encode()).hexdigest()[:8]}]"
    return f"{base} {scenario_description}{suffix}"

def generate_step_state(step_id: int, scenario_type: str, scenario_description: str, seed: int) -> StepState:
    """
    Generate a single step state based on the scenario.
    """
    random.seed(seed + step_id)

    action, target, result, error = "", "", "", None

    if "SP_01" in scenario_description:
        # Edit file A.txt after it was deleted
        if step_id == 1:
            action = "delete"
            target = "A.txt"
            result = "success"
        elif step_id == 2:
            action = "edit"
            target = "A.txt"
            result = "failure"
            error = "FileNotFoundError: A.txt does not exist"
        else:
            action = "read"
            target = "B.txt"
            result = "success"

    elif "SP_02" in scenario_description:
        # Read variable x after reset to None
        if step_id == 1:
            action = "assign"
            target = "x"
            result = "success"
        elif step_id == 2:
            action = "reset"
            target = "x"
            result = "success"
        elif step_id == 3:
            action = "read"
            target = "x"
            result = "failure"
            error = "ValueError: x is None"
        else:
            action = "read"
            target = "y"
            result = "success"

    elif "SP_03" in scenario_description:
        # Move file B.txt to deleted directory
        if step_id == 1:
            action = "create_dir"
            target = "temp_dir"
            result = "success"
        elif step_id == 2:
            action = "delete_dir"
            target = "temp_dir"
            result = "success"
        elif step_id == 3:
            action = "move"
            target = "B.txt -> temp_dir"
            result = "failure"
            error = "FileNotFoundError: temp_dir does not exist"
        else:
            action = "read"
            target = "B.txt"
            result = "success"

    elif "SP_04" in scenario_description:
        # Write to file C.txt after handle closed
        if step_id == 1:
            action = "open"
            target = "C.txt"
            result = "success"
        elif step_id == 2:
            action = "close"
            target = "C.txt"
            result = "success"
        elif step_id == 3:
            action = "write"
            target = "C.txt"
            result = "failure"
            error = "ValueError: I/O operation on closed file"
        else:
            action = "read"
            target = "D.txt"
            result = "success"

    elif "SP_05" in scenario_description:
        # Execute command on terminated process P1
        if step_id == 1:
            action = "start"
            target = "P1"
            result = "success"
        elif step_id == 2:
            action = "terminate"
            target = "P1"
            result = "success"
        elif step_id == 3:
            action = "send_command"
            target = "P1"
            result = "failure"
            error = "ProcessLookupError: P1 is not running"
        else:
            action = "read"
            target = "log.txt"
            result = "success"

    elif "RD_01" in scenario_description:
        # Read wrong line
        if step_id == 1:
            action = "open"
            target = "A.txt"
            result = "success"
        elif step_id == 2:
            action = "read_line"
            target = "A.txt"
            result = "Line 2 (Expected Line 1)"
            error = None # Logical error, not runtime
        else:
            action = "close"
            target = "A.txt"
            result = "success"

    elif "RD_02" in scenario_description:
        # Arithmetic error
        if step_id == 1:
            action = "calculate"
            target = "sum([1, 2])"
            result = "4" # Wrong, should be 3
            error = None
        else:
            action = "return"
            target = "result"
            result = "4"

    elif "RD_03" in scenario_description:
        # Sorting error
        if step_id == 1:
            action = "sort"
            target = "[3, 1, 2]"
            result = "[1, 3, 2]" # Wrong
            error = None
        else:
            action = "return"
            target = "sorted_list"
            result = "[1, 3, 2]"

    elif "RD_04" in scenario_description:
        # Filtering error
        if step_id == 1:
            action = "filter"
            target = "[1, 2, 3] > 1"
            result = "[2]" # Wrong, missing 3
            error = None
        else:
            action = "return"
            target = "filtered_list"
            result = "[2]"

    elif "RD_05" in scenario_description:
        # Concatenation order error
        if step_id == 1:
            action = "concat"
            target = '"a" + "b"'
            result = "ba" # Wrong
            error = None
        else:
            action = "return"
            target = "string"
            result = "ba"
    else:
        # Fallback for unknown scenarios
        action = "unknown"
        target = "unknown"
        result = "unknown"

    return StepState(
        step_id=step_id,
        action=action,
        target=target,
        result=result,
        error=error
    )

def generate_trace(scenario_type: str, scenario_description: str, seed: int) -> Dict[str, Any]:
    """
    Generate a full execution trace for a given scenario.
    """
    random.seed(seed)
    task_id = f"trace_{hashlib.sha256(str(seed).encode()).hexdigest()[:8]}"
    task_description = generate_task_description(scenario_type, scenario_description, seed)

    # Generate 3-5 steps based on the scenario
    num_steps = 3 if "SP" in scenario_description or "RD" in scenario_description else 4
    steps = []
    for i in range(num_steps):
        step = generate_step_state(i, scenario_type, scenario_description, seed)
        steps.append({
            "step_id": step.step_id,
            "action": step.action,
            "target": step.target,
            "result": step.result,
            "error": step.error
        })

    final_state = {
        "status": "completed_with_errors" if any(s.get("error") for s in steps) else "success",
        "errors": [s.get("error") for s in steps if s.get("error")]
    }

    return {
        "task_id": task_id,
        "task_description": task_description,
        "steps": steps,
        "final_state": final_state,
        "ground_truth": scenario_type
    }
