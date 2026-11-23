"""
Oracle-Symbolic Agent Inference Module (Secondary Diagnostic Tool)

This module implements the Oracle-Symbolic agent, which simulates a perfect policy
by retrieving ground-truth action sequences from the dataset. This is a secondary
diagnostic tool used to isolate reasoning/perception limitations from policy limitations.

It does NOT replace the Baseline-Guava (Visual) agent for primary success criteria.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.models import TaskOutcome, serialize_outcome
from utils.exceptions import DatasetUnavailableError
from utils.config import get_path


class OracleSymbolicAgent:
    """
    Oracle-Symbolic Agent: Simulates a perfect policy by retrieving ground-truth actions.
    
    This agent assumes perfect perception and perfect reasoning. It simply looks up
    the correct action sequence for a given task/trajectory and executes it.
    """

    def __init__(self, ground_truth_actions_path: Optional[Path] = None):
        """
        Initialize the Oracle agent.

        Args:
            ground_truth_actions_path: Path to the ground-truth actions JSON file.
                                       Defaults to data/raw/guava/ground_truth_actions.json
        """
        if ground_truth_actions_path is None:
            ground_truth_actions_path = get_path("raw", "guava", "ground_truth_actions.json")
        
        self.ground_truth_path = Path(ground_truth_actions_path)
        self.actions_db: Dict[str, List[Dict[str, Any]]] = {}
        self._load_actions_db()

    def _load_actions_db(self) -> None:
        """
        Load the ground-truth actions database from disk.
        
        Raises:
            DatasetUnavailableError: If the ground-truth actions file is missing or invalid.
        """
        if not self.ground_truth_path.exists():
            raise DatasetUnavailableError(
                f"Ground-truth actions file not found at {self.ground_truth_path}. "
                "Please ensure T013/T014 have completed successfully and generated "
                "data/raw/guava/ground_truth_actions.json. "
                "Oracle-Symbolic agent cannot run without this file."
            )

        try:
            with open(self.ground_truth_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Expected format: {"trajectory_id": [{"action": "...", "params": {...}}, ...]}
            if not isinstance(data, dict):
                raise DatasetUnavailableError(
                    f"Invalid format in {self.ground_truth_path}. Expected a JSON object mapping "
                    "trajectory_id to action lists."
                )
            
            self.actions_db = data
            print(f"[Oracle Agent] Loaded {len(self.actions_db)} trajectory action sequences.")
        except json.JSONDecodeError as e:
            raise DatasetUnavailableError(
                f"Failed to parse ground-truth actions JSON: {e}"
            ) from e

    def get_action_sequence(self, trajectory_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve the ground-truth action sequence for a specific trajectory.

        Args:
            trajectory_id: The ID of the trajectory.

        Returns:
            List of action dictionaries.

        Raises:
            KeyError: If the trajectory_id is not found in the database.
        """
        if trajectory_id not in self.actions_db:
            raise KeyError(f"Trajectory ID '{trajectory_id}' not found in ground-truth actions database.")
        return self.actions_db[trajectory_id]

    def simulate_execution(self, trajectory_id: str) -> TaskOutcome:
        """
        Simulate the execution of the ground-truth action sequence for a trajectory.
        
        Since this is an Oracle, it assumes perfect execution. The outcome is always
        success unless the trajectory itself is marked as impossible in the data.

        Args:
            trajectory_id: The ID of the trajectory to simulate.

        Returns:
            TaskOutcome object representing the simulated execution.
        """
        start_time = time.time()
        
        try:
            actions = self.get_action_sequence(trajectory_id)
            
            # Simulate execution time (very fast, as it's just a lookup)
            # In a real environment, this would involve physics simulation time,
            # but here we just record the lookup time.
            execution_time = time.time() - start_time
            
            # Determine success based on the presence of actions.
            # If the trajectory has actions defined, the Oracle "succeeds".
            # We assume the ground-truth actions are by definition successful.
            success = len(actions) > 0
            
            outcome = TaskOutcome(
                trajectory_id=trajectory_id,
                agent_type="Oracle-Symbolic",
                success=success,
                steps_executed=len(actions),
                total_actions=len(actions),
                execution_time_ms=round(execution_time * 1000, 3),
                failure_category=None,
                error_message=None,
                metadata={
                    "oracle_mode": True,
                    "actions_retrieved": True,
                    "policy_limitation_isolated": True
                }
            )
            
            return outcome

        except KeyError as e:
            outcome = TaskOutcome(
                trajectory_id=trajectory_id,
                agent_type="Oracle-Symbolic",
                success=False,
                steps_executed=0,
                total_actions=0,
                execution_time_ms=round((time.time() - start_time) * 1000, 3),
                failure_category="data_missing",
                error_message=str(e),
                metadata={"oracle_mode": True, "actions_retrieved": False}
            )
            return outcome


def run_oracle_evaluation(
    trajectory_ids: List[str],
    output_path: Optional[Path] = None
) -> List[TaskOutcome]:
    """
    Run the Oracle-Symbolic agent on a list of trajectories.

    Args:
        trajectory_ids: List of trajectory IDs to evaluate.
        output_path: Optional path to write the results JSON. Defaults to 
                    data/artifacts/oracle_evaluation_results.json.

    Returns:
        List of TaskOutcome objects.
    """
    if output_path is None:
        output_path = get_path("artifacts", "oracle_evaluation_results.json")

    print(f"[Oracle Evaluation] Starting evaluation on {len(trajectory_ids)} trajectories...")
    
    agent = OracleSymbolicAgent()
    outcomes = []

    for tid in trajectory_ids:
        outcome = agent.simulate_execution(tid)
        outcomes.append(outcome)
        
        status = "SUCCESS" if outcome.success else "FAILED"
        print(f"  - {tid}: {status} ({outcome.steps_executed} steps, {outcome.execution_time_ms}ms)")

    # Write results to disk
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        serialized = [serialize_outcome(o) for o in outcomes]
        json.dump(serialized, f, indent=2)
    
    print(f"[Oracle Evaluation] Results written to {output_path}")
    return outcomes


def main():
    """
    Main entry point for the Oracle-Symbolic evaluation script.
    
    Reads a list of trajectory IDs from a config or defaults to a sample set,
    runs the evaluation, and saves results.
    """
    # Example: Load trajectory IDs from a config file or hardcode for demo
    # In a real pipeline, this would read from the held-out test set defined in config
    config_path = get_path("config", "evaluation_config.json")
    
    trajectory_ids = []
    
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                trajectory_ids = config.get("test_trajectory_ids", [])
        except Exception as e:
            print(f"[Warning] Could not load evaluation config: {e}")
    
    # Fallback: If no IDs provided, try to infer from existing symbolic data
    if not trajectory_ids:
        symbolic_dir = get_path("processed", "symbolic_guava")
        if symbolic_dir.exists():
            files = list(symbolic_dir.glob("*.json"))
            trajectory_ids = [f.stem for f in files[:10]]  # Take first 10 for demo
            print(f"[Info] Using first 10 symbolic trajectories as test set: {trajectory_ids}")
        else:
            print("[Error] No trajectory IDs found. Please ensure symbolic data exists or provide config.")
            sys.exit(1)

    try:
        run_oracle_evaluation(trajectory_ids)
    except DatasetUnavailableError as e:
        print(f"[Error] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()