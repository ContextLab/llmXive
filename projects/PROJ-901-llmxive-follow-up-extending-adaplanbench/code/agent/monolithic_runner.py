"""
Runner script for the Monolithic Agent baseline.
Executes the monolithic agent on the filtered dataset and logs results.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, get_model_config, set_all_seeds
from agent.monolithic import MonolithicAgent, MonolithicAgentConfig
from agent.base import TaskContext, ExecutionResult, ViolationType

def load_filtered_tasks(input_path: str) -> List[Dict[str, Any]]:
    """Load filtered tasks from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    # Ensure progressive_constraints is parsed if it's a string representation of a list
    if 'progressive_constraints' in df.columns:
        def parse_constraints(val):
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                # Handle string representation of list
                val = val.strip()
                if val.startswith('[') and val.endswith(']'):
                    try:
                        # Safe evaluation of list string
                        return eval(val, {"__builtins__": {}}, {})
                    except Exception:
                        return [val] if val else []
            return [val] if val else []
        
        df['progressive_constraints'] = df['progressive_constraints'].apply(parse_constraints)
    
    tasks = df.to_dict('records')
    return tasks

def run_monolithic(dataset: List[Dict[str, Any]], model_name: str) -> List[Dict[str, Any]]:
    """
    Execute the monolithic agent on the provided dataset.

    Args:
        dataset: List of task dictionaries.
        model_name: Name of the model to use.

    Returns:
        List of execution log entries conforming to the schema.
    """
    paths = get_paths()
    model_config = get_model_config()

    # Configure agent
    agent_config = MonolithicAgentConfig(
        model_name=model_name,
        max_tokens=model_config.MAX_TOKENS,
        temperature=model_config.TEMPERATURE,
        device=model_config.DEVICE,
        precision=model_config.PRECISION
    )

    agent = MonolithicAgent(agent_config)
    results = []

    for task in dataset:
        task_id = task.get('task_id', 'unknown')
        constraints = task.get('progressive_constraints', [])
        if isinstance(constraints, str):
            try:
                constraints = eval(constraints, {"__builtins__": {}}, {})
            except Exception:
                constraints = [constraints] if constraints else []
        
        constraint_count = len(constraints) if constraints else 0
        raw_prompt = task.get('raw_prompt', '')

        # Create task context
        context = TaskContext(
            task_id=task_id,
            raw_prompt=raw_prompt,
            constraints=constraints,
            constraint_count=constraint_count
        )

        try:
            # Execute agent
            result: ExecutionResult = agent.execute(context)

            # Determine violations
            violation_bool = False
            violation_reason = None
            if result.violations:
                violation_bool = True
                # Aggregate reasons
                reasons = [v.reason for v in result.violations if v.reason]
                violation_reason = "; ".join(reasons) if reasons else "Constraint violation detected"

            log_entry = {
                "task_id": task_id,
                "constraint_count": constraint_count,
                "generated_plan": result.generated_plan if result.generated_plan else "",
                "violation_boolean": violation_bool,
                "violation_reason": violation_reason,
                "final_score": float(result.final_score) if result.final_score is not None else 0.0
            }
            results.append(log_entry)

        except Exception as e:
            # Log error but continue
            print(f"Error processing task {task_id}: {e}", file=sys.stderr)
            log_entry = {
                "task_id": task_id,
                "constraint_count": constraint_count,
                "generated_plan": "",
                "violation_boolean": True,
                "violation_reason": f"Execution error: {str(e)}",
                "final_score": 0.0
            }
            results.append(log_entry)

    return results

def main():
    parser = argparse.ArgumentParser(description="Run Monolithic Agent on filtered dataset")
    parser.add_argument("--input", type=str, default="data/processed/filtered_tasks.csv",
                        help="Path to input filtered tasks CSV")
    parser.add_argument("--output", type=str, default="data/processed/monolithic_logs.json",
                        help="Path to output logs JSON")
    parser.add_argument("--model", type=str, default="microsoft/phi-2",
                        help="Model name to use")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # Set seeds
    set_all_seeds(args.seed)

    paths = get_paths()

    # Load dataset
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading tasks from {args.input}...")
    dataset = load_filtered_tasks(args.input)
    print(f"Loaded {len(dataset)} tasks.")

    # Run monolithic agent
    print(f"Running monolithic agent with model '{args.model}'...")
    logs = run_monolithic(dataset, args.model)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

    print(f"Results written to {output_path}")
    print(f"Processed {len(logs)} tasks.")

if __name__ == "__main__":
    main()