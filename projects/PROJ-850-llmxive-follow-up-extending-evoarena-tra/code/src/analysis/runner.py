"""
Experiment runner for executing tasks on agent variants.

This module orchestrates the execution of tasks on different agent variants
and logs the results.
"""
import json
import time
import csv
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.utils.seeding import set_deterministic_seed
from src.agents.evomem_all import EvoMemAll
from src.agents.evomem_conflict import EvoMemConflict


def load_tasks(tasks_path: str = 'data/raw/terminal_bench_evo.jsonl') -> List[Dict[str, Any]]:
    """
    Load tasks from a JSONL file.
    
    Args:
        tasks_path (str): Path to the tasks file.
    
    Returns:
        List[Dict[str, Any]]: List of loaded tasks.
    """
    tasks = []
    
    if not Path(tasks_path).exists():
        print(f"Warning: Tasks file not found at {tasks_path}")
        return tasks
    
    with open(tasks_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    
    return tasks


def execute_task_on_agent(task: Dict[str, Any], agent, variant_name: str) -> Dict[str, Any]:
    """
    Execute a single task on an agent.
    
    Args:
        task (Dict[str, Any]): The task to execute.
        agent: The agent to use for execution.
        variant_name (str): Name of the agent variant.
    
    Returns:
        Dict[str, Any]: Execution results.
    """
    # Reset agent metrics
    agent.reset_metrics()
    
    # Build task context
    task_context = {
        'patches': task.get('state_patches', [])
    }
    
    # Retrieve patches
    start_time = time.time()
    patches = agent.retrieve_patches(task_context)
    retrieval_time = time.time() - start_time
    
    # Execute task
    start_time = time.time()
    result = agent.execute_task(task, patches)
    execution_time = time.time() - start_time
    
    # Compile results
    results = {
        'task_id': task.get('task_id', 'unknown'),
        'agent_variant': variant_name,
        'context_tokens': result.get('context_tokens', 0),
        'inference_time': execution_time,
        'success_status': result.get('success_status', False),
        'retrieval_time': retrieval_time,
        'output': result.get('output', '')
    }
    
    return results


def run_experiment(config: str = 'full'):
    """
    Run the full experiment on all agent variants.
    
    Args:
        config (str): Configuration to use ('quick' or 'full').
    """
    # Set deterministic seed
    set_deterministic_seed(42)
    
    # Load tasks
    tasks = load_tasks()
    
    if not tasks:
        print("No tasks found. Exiting.")
        return
    
    # Limit tasks for quick config
    if config == 'quick':
        tasks = tasks[:5]
    
    # Initialize agents
    agents = {
        'EvoMem-All': EvoMemAll(n_patches=10),
        'EvoMem-Conflict': EvoMemConflict(n_patches=10)
    }
    
    # Execute tasks on each agent
    all_results = []
    
    for variant_name, agent in agents.items():
        print(f"Running {variant_name} on {len(tasks)} tasks...")
        
        for task in tasks:
            result = execute_task_on_agent(task, agent, variant_name)
            all_results.append(result)
            print(f"  Completed task {result['task_id']}")
    
    # Write results to CSV
    write_results_to_csv(all_results)
    
    print(f"Experiment completed. Results saved to data/logs/full_run.csv")


def write_results_to_csv(results: List[Dict[str, Any]], output_path: str = 'data/logs/full_run.csv'):
    """
    Write experiment results to a CSV file.
    
    Args:
        results (List[Dict[str, Any]]): List of result dictionaries.
        output_path (str): Path to the output CSV file.
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    if not results:
        print("No results to write.")
        return
    
    # Get fieldnames from first result
    fieldnames = list(results[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def main(config: str = 'full'):
    """Main entry point for the experiment runner."""
    run_experiment(config)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run EvoMem experiments')
    parser.add_argument('--config', type=str, default='full',
                      choices=['quick', 'full'],
                      help='Configuration to use for the experiment')
    
    args = parser.parse_args()
    main(args.config)
