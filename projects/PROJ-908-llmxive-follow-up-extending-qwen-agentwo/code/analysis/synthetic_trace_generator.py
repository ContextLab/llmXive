"""
Synthetic Control Trace Generator for T019.

Generates N=500 traces with pre-determined logical patterns for validation
of the Pattern Reproduction Precision metric (T026).

This script produces `data/raw/synthetic_control_traces.json`.
"""
import json
import logging
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Seed for reproducibility
RANDOM_SEED = 42
NUM_TRACES = 500

@dataclass
class CoTStep:
    """Represents a single step in a Chain-of-Thought trace."""
    step_id: int
    thought: str
    action: str
    observation: Optional[str] = None

@dataclass
class SyntheticTrace:
    """Represents a full synthetic trace with a known pattern."""
    trace_id: str
    pattern_id: str
    task_description: str
    steps: List[Dict[str, Any]]
    expected_outcome: str
    metadata: Dict[str, Any]

class SyntheticTraceGenerator:
    """
    Generates synthetic control traces with deterministic logical patterns.
    
    Patterns include:
    - P01: Linear Sequential (A -> B -> C)
    - P02: Conditional Branch (If X then Y else Z)
    - P03: Loop/Iteration (Repeat N times)
    - P04: Backtracking (Try A, fail, try B)
    - P05: Parallel Execution (Do A and B concurrently)
    """

    def __init__(self, seed: int = RANDOM_SEED):
        self.seed = seed
        random.seed(seed)
        self.pattern_templates = {
            "P01": self._generate_linear,
            "P02": self._generate_conditional,
            "P03": self._generate_loop,
            "P04": self._generate_backtrack,
            "P05": self._generate_parallel
        }
        self.pattern_ids = list(self.pattern_templates.keys())

    def _generate_linear(self, trace_id: str, task_base: str) -> SyntheticTrace:
        """Pattern P01: Linear Sequential execution."""
        steps = [
            {"step_id": 1, "thought": "Analyze the initial state of the environment.", "action": "observe", "observation": "Environment initialized."},
            {"step_id": 2, "thought": "Identify the first required action to reach the goal.", "action": "plan", "observation": "Goal identified: Retrieve Item A."},
            {"step_id": 3, "thought": "Execute the first action: Move to location A.", "action": "move", "observation": "Arrived at location A."},
            {"step_id": 4, "thought": "Execute the second action: Pick up Item A.", "action": "pickup", "observation": "Item A acquired."},
            {"step_id": 5, "thought": "Execute the final action: Move to goal location.", "action": "move", "observation": "Goal reached."}
        ]
        return SyntheticTrace(
            trace_id=trace_id,
            pattern_id="P01",
            task_description=f"{task_base} (Linear Sequence)",
            steps=steps,
            expected_outcome="Success: Linear path completed without deviation.",
            metadata={"complexity": "low", "steps_count": 5}
        )

    def _generate_conditional(self, trace_id: str, task_base: str) -> SyntheticTrace:
        """Pattern P02: Conditional Branching."""
        steps = [
            {"step_id": 1, "thought": "Check the status of the resource.", "action": "query", "observation": "Resource status: Available."},
            {"step_id": 2, "thought": "Since resource is available, proceed with standard protocol.", "action": "branch", "observation": "Branch taken: Standard Protocol."},
            {"step_id": 3, "thought": "Execute standard protocol action.", "action": "execute", "observation": "Protocol completed."},
            {"step_id": 4, "thought": "Verify completion.", "action": "verify", "observation": "Task verified."}
        ]
        # Add a slight variation in thought to make it look real
        steps[1]["thought"] = f"Since resource is available (check #{random.randint(10,99)}), proceed with standard protocol."
        
        return SyntheticTrace(
            trace_id=trace_id,
            pattern_id="P02",
            task_description=f"{task_base} (Conditional Branch)",
            steps=steps,
            expected_outcome="Success: Conditional logic resolved to 'Available' branch.",
            metadata={"complexity": "medium", "steps_count": 4, "branch_taken": "available"}
        )

    def _generate_loop(self, trace_id: str, task_base: str) -> SyntheticTrace:
        """Pattern P03: Iterative Loop."""
        loop_count = random.randint(3, 5)
        steps = [
            {"step_id": 1, "thought": "Initialize loop counter to 0.", "action": "init", "observation": "Counter = 0."}
        ]
        for i in range(1, loop_count + 1):
            steps.append({
                "step_id": 1 + i,
                "thought": f"Iteration {i}: Perform processing task.",
                "action": "process",
                "observation": f"Item {i} processed."
            })
        steps.append({
            "step_id": 1 + loop_count + 1,
            "thought": f"Loop complete after {loop_count} iterations.",
            "action": "finalize",
            "observation": "All items processed."
        })
        
        return SyntheticTrace(
            trace_id=trace_id,
            pattern_id="P03",
            task_description=f"{task_base} (Loop Iteration)",
            steps=steps,
            expected_outcome=f"Success: Loop executed {loop_count} times.",
            metadata={"complexity": "medium", "steps_count": len(steps), "iterations": loop_count}
        )

    def _generate_backtrack(self, trace_id: str, task_base: str) -> SyntheticTrace:
        """Pattern P04: Backtracking/Recovery."""
        steps = [
            {"step_id": 1, "thought": "Attempt primary path to goal.", "action": "move", "observation": "Path blocked."},
            {"step_id": 2, "thought": "Primary path failed. Backtrack to previous node.", "action": "backtrack", "observation": "Backtracked to start."},
            {"step_id": 3, "thought": "Identify alternative path.", "action": "plan", "observation": "Alternative path found."},
            {"step_id": 4, "thought": "Execute alternative path.", "action": "move", "observation": "Path clear."},
            {"step_id": 5, "thought": "Complete task via alternative path.", "action": "finish", "observation": "Goal reached."}
        ]
        return SyntheticTrace(
            trace_id=trace_id,
            pattern_id="P04",
            task_description=f"{task_base} (Backtracking Recovery)",
            steps=steps,
            expected_outcome="Success: Recovery from failure state achieved.",
            metadata={"complexity": "high", "steps_count": 5, "failures": 1}
        )

    def _generate_parallel(self, trace_id: str, task_base: str) -> SyntheticTrace:
        """Pattern P05: Parallel Execution Simulation."""
        steps = [
            {"step_id": 1, "thought": "Split task into sub-task A and sub-task B.", "action": "fork", "observation": "Threads spawned."},
            {"step_id": 2, "thought": "Execute sub-task A: Gather data.", "action": "gather", "observation": "Data gathered."},
            {"step_id": 3, "thought": "Execute sub-task B: Process data.", "action": "process", "observation": "Data processed."},
            {"step_id": 4, "thought": "Wait for both sub-tasks to complete.", "action": "join", "observation": "Both tasks done."},
            {"step_id": 5, "thought": "Merge results.", "action": "merge", "observation": "Results merged."}
        ]
        return SyntheticTrace(
            trace_id=trace_id,
            pattern_id="P05",
            task_description=f"{task_base} (Parallel Execution)",
            steps=steps,
            expected_outcome="Success: Parallel tasks synchronized and merged.",
            metadata={"complexity": "high", "steps_count": 5, "threads": 2}
        )

    def generate_trace(self, trace_id: str, pattern_id: Optional[str] = None) -> SyntheticTrace:
        """Generate a single trace with a specific or random pattern."""
        if pattern_id is None:
            pattern_id = random.choice(self.pattern_ids)
        
        task_bases = [
            "Navigate the grid world to retrieve the key.",
            "Assemble the components in the correct order.",
            "Solve the logical puzzle by eliminating options.",
            "Retrieve the artifact from the guarded room.",
            "Coordinate the team to reach the extraction point."
        ]
        task_base = random.choice(task_bases)
        
        generator_func = self.pattern_templates[pattern_id]
        return generator_func(trace_id, task_base)

    def generate_dataset(self, num_traces: int, output_path: Path) -> None:
        """Generate the full dataset and write to disk."""
        logger.info(f"Generating {num_traces} synthetic control traces with seed {self.seed}...")
        
        traces = []
        # Ensure we distribute patterns somewhat evenly
        pattern_counts = {pid: 0 for pid in self.pattern_ids}
        
        for i in range(num_traces):
            # Round-robin assignment to ensure coverage, then randomize
            if i < num_traces:
                # Distribute evenly first
                assigned_pattern = self.pattern_ids[i % len(self.pattern_ids)]
            else:
                assigned_pattern = None
            
            trace = self.generate_trace(trace_id=f"synth_{i:04d}", pattern_id=assigned_pattern)
            traces.append(asdict(trace))
            pattern_counts[trace.pattern_id] += 1

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(traces, f, indent=2)
        
        logger.info(f"Successfully wrote {len(traces)} traces to {output_path}")
        logger.info(f"Pattern distribution: {pattern_counts}")

def main():
    output_path = Path("data/raw/synthetic_control_traces.json")
    generator = SyntheticTraceGenerator(seed=RANDOM_SEED)
    generator.generate_dataset(NUM_TRACES, output_path)

if __name__ == "__main__":
    main()
