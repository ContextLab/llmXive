"""
Monolithic Baseline Runner for AdaPlanBench.

Executes the monolithic agent (single SLM pass) on the filtered dataset
and logs results conforming to the execution-log schema.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import torch

from config import get_paths, get_model_config
from agent.monolithic import MonolithicAgent, MonolithicAgentConfig
from agent.judges import AdaPlanJudge
from agent.base import ExecutionResult, TaskContext, ViolationType


def load_filtered_tasks(input_path: str) -> List[Dict[str, Any]]:
    """
    Load tasks from the filtered CSV.

    Args:
        input_path: Path to data/processed/filtered_tasks.csv

    Returns:
        List of task dictionaries.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered dataset not found at {input_path}. "
                                "Run dataset loader/filtering first.")

    df = pd.read_csv(input_path)
    # Convert rows to dicts, ensuring constraint lists are parsed if stored as strings
    tasks = []
    for _, row in df.iterrows():
        task = row.to_dict()
        # Handle potential string representation of lists
        if isinstance(task.get('progressive_constraints'), str):
            import ast
            try:
                task['progressive_constraints'] = ast.literal_eval(task['progressive_constraints'])
            except (ValueError, SyntaxError):
                task['progressive_constraints'] = []
        
        # Ensure constraint_count is an integer
        if 'constraint_count' in task:
            task['constraint_count'] = int(task['constraint_count'])
        
        tasks.append(task)
    
    return tasks


def run_monolithic(dataset: List[Dict[str, Any]], model_name: str = "phi-3-mini") -> List[Dict[str, Any]]:
    """
    Execute the monolithic baseline on the provided dataset.

    Args:
        dataset: List of task dictionaries.
        model_name: Name of the model to use (default: phi-3-mini).

    Returns:
        List of execution log entries conforming to the schema.
    """
    paths = get_paths()
    model_config = get_model_config()
    
    # Initialize the monolithic agent
    agent_config = MonolithicAgentConfig(
        model_name=model_name,
        device="cuda" if torch.cuda.is_available() else "cpu",
        temperature=0.7,
        max_tokens=512
    )
    agent = MonolithicAgent(agent_config)
    
    # Initialize the judge for scoring
    judge = AdaPlanJudge()
    
    logs = []
    
    for task in dataset:
        task_id = task.get('task_id', 'unknown')
        constraint_count = task.get('constraint_count', 0)
        progressive_constraints = task.get('progressive_constraints', [])
        
        # Prepare context
        context = TaskContext(
            task_id=task_id,
            initial_state=task.get('initial_state', ''),
            goal=task.get('goal', ''),
            constraints=progressive_constraints,
            step_history=[]
        )
        
        try:
            # Execute monolithic generation
            # The monolithic agent generates a full plan in one go
            result: ExecutionResult = agent.generate_plan(context)
            
            generated_plan = result.plan_text
            
            # Evaluate with the judge
            # The judge determines violation and final score based on the plan vs constraints
            evaluation = judge.evaluate(task, generated_plan)
            
            violation_boolean = evaluation.get('violation', False)
            violation_reason = evaluation.get('reason', None)
            final_score = evaluation.get('score', 0.0)
            
            log_entry = {
                "task_id": task_id,
                "constraint_count": constraint_count,
                "generated_plan": generated_plan,
                "violation_boolean": violation_boolean,
                "violation_reason": violation_reason,
                "final_score": final_score
            }
            
        except Exception as e:
            # Log failure for this task but continue with others
            log_entry = {
                "task_id": task_id,
                "constraint_count": constraint_count,
                "generated_plan": f"ERROR: {str(e)}",
                "violation_boolean": True,
                "violation_reason": f"Execution error: {str(e)}",
                "final_score": 0.0
            }
        
        logs.append(log_entry)
    
    return logs


def main():
    """
    Main entry point for the monolithic runner script.
    """
    parser = argparse.ArgumentParser(description="Run monolithic baseline on filtered AdaPlanBench tasks.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/filtered_tasks.csv",
        help="Path to the filtered tasks CSV."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/monolithic_logs.json",
        help="Path to save the execution logs JSON."
    )
    parser.add_argument(
        "--model",
        type=str,
        default="phi-3-mini",
        help="Model name to use for the monolithic agent."
    )
    
    args = parser.parse_args()
    
    print(f"Loading filtered dataset from {args.input}...")
    try:
        dataset = load_filtered_tasks(args.input)
        print(f"Loaded {len(dataset)} tasks.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    print(f"Running monolithic agent on {len(dataset)} tasks...")
    logs = run_monolithic(dataset, model_name=args.model)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Writing {len(logs)} logs to {args.output}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
    
    print("Monolithic execution complete.")


if __name__ == "__main__":
    main()