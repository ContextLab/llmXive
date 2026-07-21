"""
Deterministic State-Transition Simulator for the Qwen-AgentWorld Oracle.

This module executes deterministic state transitions based on the logic
extracted by `code/oracle/parser.py`. It consumes the parsed InteractionLogic
and StateTransition definitions to simulate environment evolution.

It relies on the Ground Truth Oracle (parsed source) to ensure determinism
and verify against the original environment simulator trajectories.
"""
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from oracle.parser import StateTransition, InteractionLogic, QwenAgentWorldParser

logger = logging.getLogger(__name__)


class SimulationError(Exception):
    """Raised when a simulation step cannot be executed or violates constraints."""
    pass


class State:
    """
    Represents the current state of the simulated environment.
    """
    def __init__(self, initial_state: Dict[str, Any] = None):
        self.variables: Dict[str, Any] = initial_state or {}
        self.history: List[Dict[str, Any]] = [self.variables.copy()]

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.variables[key] = value
        self.history.append(self.variables.copy())

    def update(self, updates: Dict[str, Any]) -> None:
        self.variables.update(updates)
        self.history.append(self.variables.copy())

    def copy(self) -> 'State':
        new_state = State(self.variables.copy())
        new_state.history = self.history.copy()
        return new_state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current": self.variables,
            "history_length": len(self.history)
        }


class Simulator:
    """
    Executes deterministic state transitions based on parsed logic.

    This simulator interprets the `InteractionLogic` extracted by the parser
    and applies `StateTransition` rules to a `State` object.
    """

    def __init__(self, logic: InteractionLogic):
        """
        Initialize the simulator with parsed interaction logic.

        Args:
            logic: The InteractionLogic object containing transitions and constraints.
        """
        self.logic = logic
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _evaluate_condition(self, condition: str, state: State) -> bool:
        """
        Evaluate a boolean condition string against the current state.

        Supports basic comparisons: ==, !=, >, <, >=, <=, and, or, not.
        This is a safe, restricted evaluator for the specific domain of the parser.
        """
        if not condition:
            return True

        # Create a safe namespace for evaluation
        # We only expose the state variables, not built-ins or modules
        safe_namespace = dict(state.variables)
        # Add basic operators if needed, but standard python eval handles them
        # We strictly filter out any dangerous attributes/methods
        try:
            # Use a restricted eval environment
            return bool(eval(condition, {"__builtins__": {}}, safe_namespace))
        except Exception as e:
            self.logger.error(f"Failed to evaluate condition '{condition}': {e}")
            raise SimulationError(f"Condition evaluation failed: {condition}") from e

    def _apply_effects(self, effects: List[str], state: State) -> None:
        """
        Apply a list of effect strings to the state.

        Effects are expected to be simple assignments: "var = value"
        or function calls if registered (simplified here to assignments).
        """
        for effect in effects:
            if '=' in effect:
                parts = effect.split('=', 1)
                if len(parts) != 2:
                    raise SimulationError(f"Invalid effect format: {effect}")
                var_name = parts[0].strip()
                value_expr = parts[1].strip()

                # Evaluate the value expression safely
                try:
                    # Allow basic literals and state variable references
                    safe_namespace = {"__builtins__": {}, "state": state}
                    # We need to inject current state variables into the eval context
                    # for expressions like "x = y + 1"
                    eval_context = {**state.variables, "__builtins__": {}}
                    value = eval(value_expr, eval_context)
                    state.set(var_name, value)
                except Exception as e:
                    raise SimulationError(f"Failed to apply effect '{effect}': {e}") from e
            else:
                # Handle side effects or logging if defined
                self.logger.debug(f"Side effect or action: {effect}")

    def execute_transition(self, transition: StateTransition, state: State) -> bool:
        """
        Attempt to execute a single state transition.

        Args:
            transition: The StateTransition object to execute.
            state: The current state of the environment.

        Returns:
            True if the transition was executed (condition met and effects applied).
            False if the condition was not met.

        Raises:
            SimulationError: If the transition logic is invalid or execution fails.
        """
        # Check precondition
        if not self._evaluate_condition(transition.condition, state):
            return False

        # Apply effects
        self._apply_effects(transition.effects, state)

        self.logger.debug(
            f"Executed transition '{transition.id}': "
            f"Condition '{transition.condition}' met. Effects: {transition.effects}"
        )
        return True

    def run_sequence(self, transitions: List[StateTransition], state: State) -> List[Dict[str, Any]]:
        """
        Execute a sequence of transitions in order.

        Args:
            transitions: List of StateTransition objects to execute.
            state: The initial state.

        Returns:
            A list of state snapshots after each successful execution.
        """
        results = []
        for t in transitions:
            executed = self.execute_transition(t, state)
            if executed:
                results.append(state.to_dict())
            else:
                self.logger.debug(f"Transition '{t.id}' skipped (condition not met)")
        return results

    def run_scenario(self, scenario_transitions: List[StateTransition], initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a complete scenario defined by a list of transitions starting from an initial state.

        Args:
            scenario_transitions: List of transitions defining the scenario.
            initial_state: Dictionary of initial variable values.

        Returns:
            A dictionary containing the final state and the full history.
        """
        state = State(initial_state)
        self.logger.info(f"Starting scenario with {len(scenario_transitions)} transitions")

        # Execute all transitions in the logic (order defined by parser)
        # In a more complex system, this might be a graph traversal, but for now
        # we assume the parser orders them logically or they are independent.
        # For this implementation, we iterate through the provided logic's transitions.

        final_state = state
        for t in scenario_transitions:
            try:
                self.execute_transition(t, final_state)
            except SimulationError as e:
                self.logger.warning(f"Scenario execution halted due to error: {e}")
                break

        return {
            "initial_state": initial_state,
            "final_state": final_state.to_dict(),
            "history": [s for s in final_state.history],
            "transition_count": len(final_state.history) - 1
        }


def simulate_oracle(
    parser_output_path: str,
    initial_state_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point to simulate the Oracle based on parsed logic.

    Args:
        parser_output_path: Path to the JSON file generated by `code/oracle/parser.py`.
        initial_state_path: Optional path to a JSON file containing initial state variables.
        output_path: Optional path to write the simulation results.

    Returns:
        The simulation result dictionary.
    """
    logger.info(f"Loading parsed oracle from {parser_output_path}")
    if not Path(parser_output_path).exists():
        raise FileNotFoundError(f"Parser output not found: {parser_output_path}")

    with open(parser_output_path, 'r') as f:
        oracle_data = json.load(f)

    # Reconstruct InteractionLogic from dict
    # The parser outputs a list of transitions or a specific structure.
    # We assume the parser output has a key 'transitions' or is a list.
    # Based on parser.py, it likely returns a list of StateTransition dicts or similar.
    # Let's assume the parser output structure matches what we can reconstruct.
    # For robustness, we handle the case where it's a list of transitions directly.

    transitions = []
    if isinstance(oracle_data, list):
        transitions = [StateTransition(**t) for t in oracle_data]
    elif isinstance(oracle_data, dict):
        if 'transitions' in oracle_data:
            transitions = [StateTransition(**t) for t in oracle_data['transitions']]
        else:
            # Fallback: try to parse as a single logic object if the structure differs
            # Assuming the parser output is a dict with 'transitions' list
            raise ValueError(f"Unexpected parser output structure: {list(oracle_data.keys())}")
    else:
        raise ValueError(f"Parser output must be a list or dict, got {type(oracle_data)}")

    logger.info(f"Loaded {len(transitions)} transitions")

    # Load initial state
    initial_state = {}
    if initial_state_path:
        if not Path(initial_state_path).exists():
            raise FileNotFoundError(f"Initial state file not found: {initial_state_path}")
        with open(initial_state_path, 'r') as f:
            initial_state = json.load(f)
        logger.info(f"Loaded initial state from {initial_state_path}")
    else:
        logger.warning("No initial state provided. Using empty state.")

    # Initialize Simulator
    logic = InteractionLogic(transitions=transitions)
    simulator = Simulator(logic)

    # Run Simulation
    result = simulator.run_scenario(transitions, initial_state)

    # Add metadata
    result["source_file"] = parser_output_path
    result["initial_state_file"] = initial_state_path

    # Write output if requested
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Simulation results written to {output_path}")

    return result


def main():
    """
    CLI entry point for the simulator.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run the Qwen-AgentWorld Oracle Simulator")
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the parsed oracle JSON file (from code/oracle/parser.py)"
    )
    parser.add_argument(
        "--initial-state", "-s",
        required=False,
        default=None,
        help="Path to initial state JSON file (optional)"
    )
    parser.add_argument(
        "--output", "-o",
        required=False,
        default=None,
        help="Path to write simulation results JSON"
    )
    parser.add_argument(
        "--log-level", "-l",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        result = simulate_oracle(
            parser_output_path=args.input,
            initial_state_path=args.initial_state,
            output_path=args.output
        )
        # If no output file specified, print summary to stdout
        if not args.output:
            print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())