"""
Baseline Execution Runner.
Processes the implicit failure subset and writes logs.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from agents.baseline import BaselineAgent
from utils.config import get_path

def load_execution_tasks(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads tasks from the implicit failure subset.
    """
    if input_path is None:
        input_path = str(get_path("implicit_failure_subset"))
    
    tasks = []
    with open(input_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                tasks.append(json.loads(line))
    return tasks

def run_baseline_experiment() -> str:
    """
    Runs the baseline experiment.
    """
    tasks = load_execution_tasks()
    agent = BaselineAgent()
    
    results = agent.run(tasks)
    
    output_path = str(get_path("baseline_log"))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        for result in results:
            f.write(json.dumps(result) + "\n")
    
    return output_path

def main():
    """
    Main entry point.
    """
    path = run_baseline_experiment()
    print(f"Baseline execution log saved to {path}")

if __name__ == "__main__":
    main()
