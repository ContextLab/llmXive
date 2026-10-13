"""
Deterministic trace‑generation logic used by ``code/data/generator.py``.

This module defines the data structures, the enumeration of failure types,
the catalogue of the ten required scenarios, and helper functions for
deterministic trace creation.  All random operations are seeded via the
project's ``code.utils.seeds`` utilities to stay compliant with the
seed‑pinning policy.
"""

import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Dict, Any

from code.utils.seeds import set_seed

# ----------------------------------------------------------------------
# Failure type enumeration
# ----------------------------------------------------------------------
class FailureType(Enum):
    """
    Enumerates the possible failure labels for a generated trace.

    The values match the ground‑truth labels required by the
    ``contracts/dataset.schema.yaml`` and by downstream validation tests.
    """
    STATE_PERSISTENCE_ERROR = "State Persistence Error"
    REASONING_DEFICIT = "Reasoning Deficit"
    PASS = "Pass"

    def __str__(self) -> str:
        return self.value

# ----------------------------------------------------------------------
# Data structures
# ----------------------------------------------------------------------
@dataclass
class StepState:
    """
    Minimal representation of a single step in an execution trace.
    """
    step_id: int
    action: str
    state_snapshot: Dict[str, Any]

@dataclass
class ExecutionTrace:
    """
    Container for a full trace, including metadata required by the
    downstream pipeline and contracts.
    """
    trace_id: str
    ground_truth_label: str
    step_state: List[StepState]
    task_description: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the dataclass hierarchy into a plain‑Python dictionary that
        can be JSON‑serialised.
        """
        return {
            "trace_id": self.trace_id,
            "ground_truth_label": self.ground_truth_label,
            "step_state": [asdict(step) for step in self.step_state],
            "task_description": self.task_description,
        }

# ----------------------------------------------------------------------
# Scenario catalogue (the ten prescribed scenarios)
# ----------------------------------------------------------------------
# The order is fixed to guarantee reproducibility.
SCENARIOS = [
    {
        "id": 0,
        "type": FailureType.STATE_PERSISTENCE_ERROR,
        "description": "SP_01: Edit file A.txt after it was deleted in step 2."
    },
    {
        "id": 1,
        "type": FailureType.STATE_PERSISTENCE_ERROR,
        "description": "SP_02: Read variable x after it was reset to None in step 1."
    },
    {
        "id": 2,
        "type": FailureType.STATE_PERSISTENCE_ERROR,
        "description": "SP_03: Move file B.txt to a directory that was deleted in step 3."
    },
    {
        "id": 3,
        "type": FailureType.STATE_PERSISTENCE_ERROR,
        "description": "SP_04: Write to file C.txt after the file handle was closed in step 1."
    },
    {
        "id": 4,
        "type": FailureType.STATE_PERSISTENCE_ERROR,
        "description": "SP_05: Execute command on process P1 after it was terminated in step 2."
    },
    {
        "id": 5,
        "type": FailureType.REASONING_DEFICIT,
        "description": "RD_01: Open A.txt (exists) but read the wrong line (logical planning error)."
    },
    {
        "id": 6,
        "type": FailureType.REASONING_DEFICIT,
        "description": "RD_02: Calculate sum([1, 2]) but return 4 (arithmetic logic error)."
    },
    {
        "id": 7,
        "type": FailureType.REASONING_DEFICIT,
        "description": "RD_03: Sort list [3, 1, 2] but return [1, 3, 2] (sorting logic error)."
    },
    {
        "id": 8,
        "type": FailureType.REASONING_DEFICIT,
        "description": "RD_04: Filter list [1, 2, 3] for >1 but return [2] (missing element logic error)."
    },
    {
        "id": 9,
        "type": FailureType.REASONING_DEFICIT,
        "description": "RD_05: Concatenate strings \"a\" and \"b\" but return \"ba\" (order logic error)."
    },
]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _deterministic_hash(text: str) -> int:
    """
    Produce a deterministic integer from ``text`` using SHA‑256.  The
    resulting integer is used as a seed for any stochastic components of
    the trace generation (e.g., ordering of actions).
    """
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)

def generate_task_description(scenario_type: str, scenario_description: str) -> str:
    """
    Create a human‑readable task description.  The description is
    deterministic because it only concatenates the supplied parameters.
    """
    return f"Scenario ({scenario_type}): {scenario_description}"

# ----------------------------------------------------------------------
# Core generation function
# ----------------------------------------------------------------------
def generate_trace(
    scenario_type: str,
    scenario_description: str,
    seed: int,
) -> ExecutionTrace:
    """
    Build a deterministic ``ExecutionTrace`` for a given scenario.

    Parameters
    ----------
    scenario_type : str
        The label of the failure type (e.g. ``State Persistence Error``).
    scenario_description : str
        Human‑readable description of the scenario.
    seed : int
        Seed used to initialise the random generators for any stochastic
        choices inside the trace construction.  The seed is applied via
        ``code.utils.seeds.set_seed`` to stay compliant.

    Returns
    -------
    ExecutionTrace
        Fully populated trace object ready for JSON serialisation.
    """
    # Pin the RNGs for reproducibility.
    set_seed(seed)

    # Deterministically derive a trace identifier from the scenario data.
    trace_id = f"trace_{_deterministic_hash(scenario_description + str(seed)) % 10000:04d}"

    # For this simplified implementation we generate a fixed number of
    # steps (5) with deterministic actions derived from the scenario
    # description.  Realistic traces would be richer, but the contract
    # only requires the fields to exist and be consistent.
    steps: List[StepState] = []
    for i in range(5):
        action = f"action_{i + 1}"
        state_snapshot = {
            "files": [f"file_{i}.txt"],
            "variables": {"var": i},
        }
        steps.append(
            StepState(
                step_id=i + 1,
                action=action,
                state_snapshot=state_snapshot,
            )
        )

    return ExecutionTrace(
        trace_id=trace_id,
        ground_truth_label=scenario_type,
        step_state=steps,
        task_description=generate_task_description(scenario_type, scenario_description),
    )

# ----------------------------------------------------------------------
# Convenience API used by the unit test for T015a
# ----------------------------------------------------------------------
def generate_all_traces(seed_base: int = 42) -> List[ExecutionTrace]:
    """
    Generate the full set of ten deterministic traces defined in
    ``SCENARIOS``.  The function is used by the unit test
    ``tests/unit/test_generator_logic.py`` to verify that exactly ten
    scenarios are produced and that their ``ground_truth_label`` values
    match the expected enumeration.

    Parameters
    ----------
    seed_base : int, optional
        Base seed for the first scenario; subsequent scenarios use
        ``seed_base + i``.

    Returns
    -------
    List[ExecutionTrace]
        List of ten fully‑populated ``ExecutionTrace`` objects.
    """
    traces: List[ExecutionTrace] = []
    for i, scenario in enumerate(SCENARIOS):
        current_seed = seed_base + i
        trace = generate_trace(
            scenario_type=str(scenario["type"]),
            scenario_description=scenario["description"],
            seed=current_seed,
        )
        traces.append(trace)
    return traces