"""
Dual-track agent orchestration module.

Implements the dual-track architecture:
1. SLM Generator: Produces a plan based on the task prompt.
2. Constraint Store: Deterministically tracks active constraints.
3. Resolver: Validates the generated plan against the store.

Logs "false_negative" if intent parsing fails (FR-008).
"""

import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from local agent modules
from agent.base import BaseAgent, ExecutionResult, TaskContext, ViolationType
from agent.constraint_store import ConstraintStore, Constraint
from agent.resolver import ConstraintResolver, ResolutionLog
from agent.monolithic import MonolithicAgent, MonolithicAgentConfig

# Import config for paths
# Note: We assume config is available in the path or we construct paths manually
# to avoid circular dependency issues if config.py is not fully ready.
# However, per API surface, we should be able to import from config if needed.
# For this module, we will rely on passed paths or standard relative logic.
try:
    from config import Paths, get_paths
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False

class DualTrackAgent:
    """
    Orchestrates the generator, store, and resolver for the dual-track architecture.
    """

    def __init__(
        self,
        generator: BaseAgent,
        store: ConstraintStore,
        resolver: ConstraintResolver,
        verbose: bool = False
    ):
        self.generator = generator
        self.store = store
        self.resolver = resolver
        self.verbose = verbose

    def execute_task(self, task_context: TaskContext) -> ExecutionResult:
        """
        Execute a single task using the dual-track architecture.

        1. Initialize the constraint store with the task's progressive constraints.
        2. Generate a plan using the SLM generator.
        3. Parse intent and resolve constraints.
        4. Log violations or corrections.
        5. Return the final execution result.
        """
        # Initialize store with constraints from context
        # The context should contain 'progressive_constraints' or similar
        constraints = task_context.metadata.get('progressive_constraints', [])
        
        # Load constraints into the store
        self.store.clear()
        for c_data in constraints:
            # Assuming c_data is a dict with 'text', 'type', etc.
            constraint = Constraint(
                id=c_data.get('id', str(len(self.store.constraints))),
                text=c_data.get('text', ''),
                constraint_type=c_data.get('type', 'general'),
                is_active=True
            )
            self.store.add(constraint)

        if self.verbose:
            print(f"Initialized store with {len(self.store.constraints)} constraints.")

        # Step 1: Generate Plan
        try:
            # The generator produces a raw plan string
            generated_plan = self.generator.generate_plan(task_context)
        except Exception as e:
            # Generator failure
            return ExecutionResult(
                task_id=task_context.task_id,
                status="error",
                generated_plan="",
                violation_type=ViolationType.GENERATOR_FAILURE,
                violation_reason=f"Generator failed: {str(e)}",
                final_score=0.0
            )

        if self.verbose:
            print(f"Generated plan: {generated_plan[:100]}...")

        # Step 2: Resolve Constraints
        # The resolver parses the intent and checks against the store
        resolution_logs = self.resolver.resolve(generated_plan, self.store)

        # Determine violations and final score
        violation_type = None
        violation_reason = None
        has_violation = False

        # Check for false negatives (intent parsing failures) per FR-008
        for log in resolution_logs:
            if log.status == "intent_parse_failure":
                # Log "false_negative" if intent parsing fails
                # This is a specific type of violation or log event
                # We treat it as a violation for the metric
                violation_type = ViolationType.FALSE_NEGATIVE
                violation_reason = f"Intent parsing failed: {log.reason}"
                has_violation = True
                break
            elif log.status == "violation_detected":
                violation_type = ViolationType.CONSTRAINT_VIOLATION
                violation_reason = log.reason
                has_violation = True
                break

        # Calculate score (simple heuristic: 1.0 if no violation, 0.0 if violation)
        # In a real scenario, this might be a weighted score based on severity
        final_score = 0.0 if has_violation else 1.0

        return ExecutionResult(
            task_id=task_context.task_id,
            status="success" if not has_violation else "violation",
            generated_plan=generated_plan,
            violation_type=violation_type,
            violation_reason=violation_reason,
            final_score=final_score,
            resolution_logs=resolution_logs
        )

def run_dual_track_experiment(
    input_path: str,
    output_path: str,
    model_name: str = "phi-3-mini",
    verbose: bool = False
) -> None:
    """
    Run the dual-track experiment on a filtered dataset.

    Args:
        input_path: Path to the filtered tasks CSV (data/processed/filtered_tasks.csv).
        output_path: Path to write the execution logs JSON (data/processed/dual_track_logs.json).
        model_name: Name of the model to use for the generator.
        verbose: Enable verbose logging.
    """
    # Setup paths
    if HAS_CONFIG:
        paths = get_paths()
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    else:
        # Fallback to relative paths if config is missing
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    tasks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)

    if not tasks:
        print(f"No tasks found in {input_path}")
        return

    # Initialize components
    # 1. Generator (MonolithicAgent as a stand-in for SLM generator)
    generator_config = MonolithicAgentConfig(model_name=model_name)
    generator = MonolithicAgent(generator_config)

    # 2. Store
    store = ConstraintStore()

    # 3. Resolver
    resolver = ConstraintResolver()

    # Create the dual-track agent
    agent = DualTrackAgent(generator, store, resolver, verbose=verbose)

    # Execute tasks
    results = []
    for task_data in tasks:
        task_id = task_data.get('task_id', 'unknown')
        prompt = task_data.get('prompt', '')
        
        # Construct TaskContext
        context = TaskContext(
            task_id=task_id,
            prompt=prompt,
            metadata=task_data
        )

        if verbose:
            print(f"Processing task: {task_id}")

        result = agent.execute_task(context)
        
        # Convert result to a serializable dict
        result_dict = {
            "task_id": result.task_id,
            "status": result.status,
            "generated_plan": result.generated_plan,
            "violation_type": result.violation_type.value if result.violation_type else None,
            "violation_reason": result.violation_reason,
            "final_score": result.final_score,
            # We might want to serialize resolution_logs differently if needed
            "resolution_count": len(result.resolution_logs) if result.resolution_logs else 0
        }
        results.append(result_dict)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"Dual-track experiment complete. Results written to {output_path}")
    print(f"Processed {len(results)} tasks.")

def main():
    """CLI entry point for running the dual-track experiment."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Dual-Track Agent Experiment")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/filtered_tasks.csv",
        help="Path to the filtered tasks CSV."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/dual_track_logs.json",
        help="Path to write the execution logs JSON."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="phi-3-mini",
        help="Model name for the generator."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging."
    )

    args = parser.parse_args()

    # Check input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    run_dual_track_experiment(
        input_path=args.input,
        output_path=args.output,
        model_name=args.model,
        verbose=args.verbose
    )

if __name__ == "__main__":
    main()