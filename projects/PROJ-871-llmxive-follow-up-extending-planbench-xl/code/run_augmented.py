import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.config import get_path, ensure_dirs_exist
from agents.augmented import AugmentedAgent
from dataset.loader import load_injected_data

def load_execution_tasks(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load tasks from the injected failure subset."""
    if input_path is None:
        input_path = get_path('data/derived/implicit_failure_subset.jsonl')
    return load_injected_data(input_path)

def run_augmented_experiment(
    tasks: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """Run the augmented agent on all tasks and write a line‑delimited JSON log."""
    if output_path is None:
        output_path = get_path('data/logs/augmented_execution.jsonl')

    # Ensure the output directory exists.
    ensure_dirs_exist(output_path.parent)

    # Initialise the augmented agent with the required configuration,
    # including the path to the failure‑signature index.
    agent = AugmentedAgent({
        'model_name': 'meta-llama/Meta-Llama-3-8B',
        'max_tokens': 512,
        'temperature': 0.7,
        'signature_index_path': get_path('data/derived/failure_signatures.json')
    })

    # Process tasks sequentially (or in batches ≤ 10) to respect the 7 GB RAM budget.
    batch_size = 10
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]
        for task in batch:
            try:
                # The AugmentedAgent API defines a ``run`` method that returns a dict
                # containing at least ``task_id``, ``final_status`` and ``signature_triggered``.
                result = agent.run(task)
            except Exception as e:
                result = {
                    'task_id': task.get('id', task.get('task_id', 'unknown')),
                    'final_status': 'error',
                    'error': str(e),
                    'agent_type': 'augmented',
                    'signature_triggered': False
                }

            # Append the result to the log file.
            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')

    return output_path

def main() -> None:
    """Entry point for the augmented runner."""
    tasks = load_execution_tasks()
    print(f"Loaded {len(tasks)} tasks for augmented execution.")
    output_file = run_augmented_experiment(tasks)
    print(f"Augmented execution completed. Log written to: {output_file}")

if __name__ == "__main__":
    main()