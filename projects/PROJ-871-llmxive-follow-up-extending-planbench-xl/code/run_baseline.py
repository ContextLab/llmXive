import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils.config import get_path, ensure_dirs_exist
from agents.baseline import BaselineAgent
from dataset.loader import load_injected_data

def load_execution_tasks(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load tasks from the injected failure subset."""
    if input_path is None:
        input_path = get_path('data/derived/implicit_failure_subset.jsonl')
    return load_injected_data(input_path)

def run_baseline_experiment(tasks: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """Run the baseline agent on all tasks."""
    if output_path is None:
        output_path = get_path('data/logs/baseline_execution.jsonl')
    
    ensure_dirs_exist(output_path.parent)
    
    agent = BaselineAgent({
        'model_name': 'meta-llama/Meta-Llama-3-8B',
        'max_tokens': 512,
        'temperature': 0.7
    })
    
    results = []
    for task in tasks:
        try:
            result = agent.execute(task)
            results.append(result)
            
            # Write incrementally to handle large datasets
            with open(output_path, 'a') as f:
                f.write(json.dumps(result) + '\n')
        except Exception as e:
            error_result = {
                'task_id': task.get('id', 'unknown'),
                'status': 'error',
                'error': str(e),
                'agent_type': 'baseline'
            }
            results.append(error_result)
            with open(output_path, 'a') as f:
                f.write(json.dumps(error_result) + '\n')
    
    return output_path

def main():
    """Main entry point for baseline execution."""
    tasks = load_execution_tasks()
    print(f"Loaded {len(tasks)} tasks")
    
    output_file = run_baseline_experiment(tasks)
    print(f"Baseline execution completed. Results saved to: {output_file}")

if __name__ == "__main__":
    main()
