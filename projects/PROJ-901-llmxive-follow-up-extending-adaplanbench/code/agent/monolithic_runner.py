"""
Monolithic Runner for AdaPlanBench Evaluation.

Executes the monolithic baseline agent on the filtered dataset and
writes execution logs conforming to the execution-log schema.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Paths, ModelConfig, get_model_config, set_all_seeds
from agent.monolithic import MonolithicAgent, MonolithicAgentConfig
from agent.base import ExecutionResult, TaskContext, ViolationType
from datasets import load_dataset


def load_filtered_tasks(task_path: str) -> List[Dict[str, Any]]:
    """
    Load the filtered tasks from the CSV produced by T014.
    Expects columns: task_id, prompt, progressive_constraints, constraint_count, etc.
    """
    import pandas as pd
    if not os.path.exists(task_path):
        raise FileNotFoundError(f"Filtered tasks file not found at {task_path}. "
                                "Ensure T014 has been run successfully.")
    
    df = pd.read_csv(task_path)
    # Parse the progressive_constraints column if it's stored as a string representation of a list
    # The loader in T012/T013 should have saved it as a list, but CSV often stringifies it.
    # We need to be robust here.
    def parse_constraints(val):
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            try:
                # Attempt to eval safely or json.loads if it's JSON formatted
                if val.startswith('[') and val.endswith(']'):
                    return eval(val) # Safe in this controlled context as it comes from our own CSV
                return []
            except Exception:
                return []
        return []

    records = df.to_dict('records')
    for record in records:
        if 'progressive_constraints' in record:
            record['progressive_constraints'] = parse_constraints(record['progressive_constraints'])
        # Ensure constraint_count is an int
        if 'constraint_count' in record:
            try:
                record['constraint_count'] = int(record['constraint_count'])
            except (ValueError, TypeError):
                record['constraint_count'] = len(record.get('progressive_constraints', []))
    
    return records


def run_monolithic(dataset: List[Dict[str, Any]], model_config: MonolithicAgentConfig) -> List[Dict[str, Any]]:
    """
    Execute the monolithic agent on each task in the dataset.
    
    Args:
        dataset: List of task dictionaries loaded from filtered_tasks.csv.
        model_config: Configuration for the monolithic agent model.
        
    Returns:
        List of log entries conforming to execution-log.schema.yaml.
    """
    # Initialize the agent
    agent = MonolithicAgent(config=model_config)
    
    logs = []
    
    for task in dataset:
        task_id = task.get('task_id', 'unknown')
        prompt = task.get('prompt', '')
        constraints = task.get('progressive_constraints', [])
        constraint_count = task.get('constraint_count', len(constraints))
        
        # Prepare context
        context = TaskContext(
            task_id=task_id,
            prompt=prompt,
            constraints=constraints,
            constraint_count=constraint_count
        )
        
        try:
            # Execute the monolithic agent
            result: ExecutionResult = agent.execute(context)
            
            # Determine violation status
            # A violation occurs if the result contains any violations or if the final plan 
            # does not satisfy the constraints (handled by agent logic, but we log what we get)
            has_violation = len(result.violations) > 0
            
            log_entry = {
                "task_id": task_id,
                "architecture": "monolithic",
                "constraint_count": constraint_count,
                "final_score": result.score,
                "has_violation": has_violation,
                "violations": [
                    {
                        "type": v.type.value,
                        "description": v.description,
                        "constraint_id": v.constraint_id
                    }
                    for v in result.violations
                ],
                "execution_time": result.execution_time,
                "raw_output": result.raw_output[:1000] if result.raw_output else "", # Truncate for log size
                "status": "success" if result.status == "success" else "failed"
            }
            logs.append(log_entry)
            
        except Exception as e:
            # Log error but continue processing other tasks
            error_log = {
                "task_id": task_id,
                "architecture": "monolithic",
                "constraint_count": constraint_count,
                "final_score": 0.0,
                "has_violation": True,
                "violations": [],
                "execution_time": 0.0,
                "raw_output": "",
                "status": "error",
                "error_message": str(e)
            }
            logs.append(error_log)
            
    return logs


def main():
    parser = argparse.ArgumentParser(description="Run Monolithic Baseline on Filtered Dataset")
    parser.add_argument("--input", type=str, default=str(Paths.PROCESSED_DATA_DIR / "filtered_tasks.csv"),
                        help="Path to the filtered tasks CSV file.")
    parser.add_argument("--output", type=str, default=str(Paths.PROCESSED_DATA_DIR / "monolithic_logs.json"),
                        help="Path to output JSON log file.")
    parser.add_argument("--model", type=str, default="phi-3-mini",
                        help="Model identifier to use.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility.")
    
    args = parser.parse_args()
    
    # Set seeds
    set_all_seeds(args.seed)
    
    # Load dataset
    print(f"Loading filtered tasks from {args.input}...")
    tasks = load_filtered_tasks(args.input)
    print(f"Loaded {len(tasks)} tasks.")
    
    if not tasks:
        print("No tasks found. Exiting.")
        return
    
    # Configure model
    # We use a minimal config for the monolithic agent to avoid heavy dependencies if not needed
    # The actual model loading happens inside MonolithicAgent
    model_cfg = MonolithicAgentConfig(
        model_name=args.model,
        max_tokens=512,
        temperature=0.0, # Deterministic for baseline
        top_p=1.0
    )
    
    print(f"Running Monolithic Agent with model: {args.model}...")
    logs = run_monolithic(tasks, model_cfg)
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully wrote {len(logs)} logs to {output_path}")


if __name__ == "__main__":
    main()
