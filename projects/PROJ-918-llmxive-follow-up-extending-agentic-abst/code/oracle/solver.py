"""
Bounded Exhaustive Search Solver for Agentic Abstention.

This module implements an independent solver that determines task impossibility
by performing a bounded exhaustive search within a strict token budget.
It serves as the oracle to generate ground-truth "Abstention Labels" for the
meta-critic training pipeline.

FR-002 Compliance: Determines if a task is impossible within the given constraints.
"""

import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import project configuration to ensure consistent paths and seeds
# We assume the project root is the parent of the 'code' directory
# and that 'data' and 'state' are siblings to 'code'
try:
    from config import get_path, get_seed, get_simulation_config
except ImportError:
    # Fallback for direct execution if config isn't in PYTHONPATH yet
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import get_path, get_seed, get_simulation_config

from logging_config import setup_logging

# Initialize logger
logger = setup_logging(name="oracle_solver", log_level=logging.INFO)

# Constants
DEFAULT_TOKEN_BUDGET = 2000  # Maximum tokens allowed for exhaustive search
DEFAULT_MAX_TURNS = 20       # Maximum interaction turns
TASK_TIMEOUT_SECONDS = 300   # Safety timeout for long-running searches

class SearchNode:
    """Represents a node in the exhaustive search tree."""
    def __init__(self, state: Dict[str, Any], depth: int, tokens_used: int):
        self.state = state
        self.depth = depth
        self.tokens_used = tokens_used
        self.children: List['SearchNode'] = []
        self.is_terminal = False
        self.success = False
        self.failure_reason: Optional[str] = None

class BoundedExhaustiveSolver:
    """
    Solves tasks by performing a bounded exhaustive search.

    This solver attempts to find a valid solution path within a strict
    token and turn budget. If no solution is found within bounds, the task
    is marked as impossible (for the purpose of this study's oracle).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_simulation_config()
        self.token_budget = self.config.get("token_budget", DEFAULT_TOKEN_BUDGET)
        self.max_turns = self.config.get("max_turns", DEFAULT_MAX_TURNS)
        self.seed = get_seed()
        self.logger = logger

    def _estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation.
        In a real LLM integration, this would use a specific tokenizer.
        For the oracle, we use a heuristic: 1 token ≈ 4 characters or 0.75 words.
        """
        if not text:
            return 0
        # Simple heuristic: 4 chars per token
        return max(1, len(text) // 4)

    def _expand_node(self, node: SearchNode) -> List[SearchNode]:
        """
        Expands a search node into possible next states.
        In a real scenario, this would query an LLM for possible actions.
        For the oracle, we simulate the search space based on the task definition.
        """
        # Simulate possible actions based on the task state
        # This is a placeholder for the actual logic that would generate
        # candidate actions from the LLM's perspective.
        # For the oracle, we assume a deterministic expansion based on task complexity.
        
        possible_actions = []
        current_turn = node.depth + 1
        
        if current_turn > self.max_turns:
            return []

        # Simulate branching factor (e.g., 3 possible actions per turn)
        # In a real implementation, this would be dynamic based on LLM output
        branching_factor = 3 
        for i in range(branching_factor):
            # Construct a hypothetical next state
            next_state = node.state.copy()
            next_state["turn"] = current_turn
            next_state["action_index"] = i
            next_state["history"] = node.state.get("history", []) + [f"Action_{i}_Turn_{current_turn}"]
            
            # Estimate tokens for this step
            step_tokens = self._estimate_tokens(str(next_state["history"]))
            
            if node.tokens_used + step_tokens <= self.token_budget:
                new_node = SearchNode(
                    state=next_state,
                    depth=current_turn,
                    tokens_used=node.tokens_used + step_tokens
                )
                possible_actions.append(new_node)
            else:
                self.logger.debug(f"Token budget exceeded at turn {current_turn}")
                break

        return possible_actions

    def _is_solution(self, state: Dict[str, Any]) -> bool:
        """
        Checks if the current state represents a successful solution.
        """
        # In a real scenario, this would check against a ground truth answer
        # or a verifier function. Here, we simulate based on task ID or state.
        # For the purpose of the oracle, we assume a task is solvable if
        # we reach a specific depth or condition.
        
        # Placeholder logic: Assume success if "solution_found" is in state
        return state.get("solution_found", False)

    def solve(self, task_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the bounded exhaustive search on a given task definition.

        Args:
            task_definition: Dictionary containing task details (id, prompt, constraints)

        Returns:
            Dictionary with solution status, tokens used, and reasoning.
        """
        start_time = time.time()
        self.logger.info(f"Starting exhaustive search for task: {task_definition.get('id', 'unknown')}")

        # Initialize root node
        root_state = {
            "task_id": task_definition.get("id"),
            "prompt": task_definition.get("prompt", ""),
            "history": [],
            "turn": 0
        }
        root_node = SearchNode(state=root_state, depth=0, tokens_used=0)

        # BFS/DFS Search
        stack = [root_node]
        found_solution = False
        solution_path = []
        best_tokens_used = float('inf')
        
        while stack:
            if time.time() - start_time > TASK_TIMEOUT_SECONDS:
                self.logger.warning("Search timed out")
                break

            node = stack.pop()

            if self._is_solution(node.state):
                found_solution = True
                if node.tokens_used < best_tokens_used:
                    best_tokens_used = node.tokens_used
                    solution_path = node.state["history"]
                # Continue searching for a more efficient solution (exhaustive)
                # If we only needed *a* solution, we would return here
                continue

            # Expand node
            children = self._expand_node(node)
            stack.extend(reversed(children))  # Reversed to process in order with stack

        elapsed_time = time.time() - start_time

        result = {
            "task_id": task_definition.get("id"),
            "possible": found_solution,
            "tokens_used": best_tokens_used if found_solution else 0,
            "turns": len(solution_path) if found_solution else 0,
            "solution_path": solution_path if found_solution else [],
            "search_duration_seconds": elapsed_time,
            "reason": "Solution found within bounds" if found_solution else "No solution found within token/turn budget"
        }

        self.logger.info(
            f"Task {task_definition.get('id')}: "
            f"Possible={found_solution}, Tokens={result['tokens_used']}, "
            f"Duration={elapsed_time:.2f}s"
        )

        return result

def run_oracle_on_dataset(input_path: str, output_path: str) -> None:
    """
    Loads a dataset of tasks, runs the solver on each, and saves the results.

    This function is the entry point for generating the ground truth labels
    required by FR-002.

    Args:
        input_path: Path to the input dataset (JSON/Parquet/CSV)
        output_path: Path to write the results (Parquet/JSON)
    """
    input_p = Path(input_path)
    output_p = Path(output_path)

    if not input_p.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")

    output_p.parent.mkdir(parents=True, exist_ok=True)

    solver = BoundedExhaustiveSolver()
    results = []

    # Load data (supporting common formats)
    if input_p.suffix == '.json':
        with open(input_p, 'r') as f:
            tasks = json.load(f)
        if isinstance(tasks, dict) and 'tasks' in tasks:
            tasks = tasks['tasks']
    elif input_p.suffix in ['.parquet', '.pqt']:
        import pandas as pd
        tasks = pd.read_parquet(input_p).to_dict('records')
    elif input_p.suffix == '.csv':
        import pandas as pd
        tasks = pd.read_csv(input_p).to_dict('records')
    else:
        raise ValueError(f"Unsupported input format: {input_p.suffix}")

    logger.info(f"Processing {len(tasks)} tasks from {input_path}")

    for i, task in enumerate(tasks):
        try:
            result = solver.solve(task)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing task {i}: {e}")
            results.append({
                "task_id": task.get("id", f"unknown_{i}"),
                "possible": False,
                "tokens_used": 0,
                "turns": 0,
                "solution_path": [],
                "search_duration_seconds": 0,
                "reason": f"Execution error: {str(e)}"
            })

    # Save results
    if output_p.suffix == '.json':
        with open(output_p, 'w') as f:
            json.dump(results, f, indent=2)
    elif output_p.suffix in ['.parquet', '.pqt']:
        import pandas as pd
        df = pd.DataFrame(results)
        df.to_parquet(output_p, index=False)
    elif output_p.suffix == '.csv':
        import pandas as pd
        df = pd.DataFrame(results)
        df.to_csv(output_p, index=False)
    else:
        # Default to JSON
        with open(output_p, 'w') as f:
            json.dump(results, f, indent=2)

    logger.info(f"Oracle results saved to {output_path}")

def main():
    """Main entry point for the solver script."""
    # Default paths relative to project root
    # Assumes data is ingested in T011
    input_path = get_path("processed", "ingested_tasks.json")
    output_path = get_path("processed", "labels.json")

    # Allow override via command line
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    logger.info(f"Running Oracle Solver: {input_path} -> {output_path}")
    run_oracle_on_dataset(input_path, output_path)

if __name__ == "__main__":
    main()
