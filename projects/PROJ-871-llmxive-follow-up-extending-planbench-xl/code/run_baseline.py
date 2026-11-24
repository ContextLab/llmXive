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

def run_baseline_experiment(
    tasks: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """Run the baseline agent on all tasks and write a line‑delimited JSON log."""
    if output_path is None:
        output_path = get_path('data/logs/baseline_execution.jsonl')

    # Ensure the output directory exists.
    ensure_dirs_exist(output_path.parent)

    # Initialise the baseline agent with the required configuration.
    agent = BaselineAgent({
        'model_name': 'meta-llama/Meta-Llama-3-8B',
        'max_tokens': 512,
        'temperature': 0.7
    })

    # Process tasks sequentially (or in small batches) to stay within RAM limits.
    for task in tasks:
        try:
            # The BaselineAgent API defines a ``run`` method that returns a dict
            # containing at least ``task_id`` and ``final_status``.
            result = agent.run(task)
        except Exception as e:
            # On unexpected errors we still emit a well‑formed JSON line.
            result = {
                'task_id': task.get('id', task.get('task_id', 'unknown')),
                'final_status': 'error',
                'error': str(e),
                'agent_type': 'baseline'
            }

        # Append the result to the log file.
        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    return output_path

def main() -> None:
    """Entry point for the baseline runner."""
    tasks = load_execution_tasks()
    print(f"Loaded {len(tasks)} tasks for baseline execution.")
    output_file = run_baseline_experiment(tasks)
    print(f"Baseline execution completed. Log written to: {output_file}")

if __name__ == "__main__":
    main()
