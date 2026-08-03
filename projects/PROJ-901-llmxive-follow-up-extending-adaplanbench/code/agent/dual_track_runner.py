"""
Dual-Track Agent Execution Runner.

Executes the dual-track architecture (SLM generator + deterministic constraint store)
on the filtered dataset and logs results conforming to the execution-log schema.
"""
import os
import sys
import json
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_paths, get_model_config, get_dataset_config, Paths, ProjectLogger, get_logger
from agent.base import TaskContext, ExecutionResult, ViolationType
from agent.constraint_store import ConstraintStore
from agent.resolver import ConstraintResolver
from agent.monolithic import MonolithicAgent, MonolithicAgentConfig
from agent.judges import AdaPlanJudge

def load_filtered_tasks_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Load the filtered tasks dataset from CSV.
    
    Args:
        dataset_path: Path to the filtered tasks CSV file.
        
    Returns:
        List of task dictionaries.
    """
    tasks = []
    logger = get_logger()
    
    if not os.path.exists(dataset_path):
        logger.error(f"Filtered tasks file not found: {dataset_path}")
        raise FileNotFoundError(f"Filtered tasks file not found: {dataset_path}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse the progressive_constraints field if it's a string representation of a list
            if 'progressive_constraints' in row:
                try:
                    # Handle string representation of list
                    if isinstance(row['progressive_constraints'], str):
                        row['progressive_constraints'] = json.loads(row['progressive_constraints'])
                    elif not isinstance(row['progressive_constraints'], list):
                        row['progressive_constraints'] = []
                except (json.JSONDecodeError, TypeError):
                    row['progressive_constraints'] = []
            
            # Ensure constraint_count is an integer
            if 'constraint_count' in row:
                try:
                    row['constraint_count'] = int(row['constraint_count'])
                except (ValueError, TypeError):
                    row['constraint_count'] = len(row.get('progressive_constraints', []))
            
            tasks.append(row)
    
    logger.info(f"Loaded {len(tasks)} tasks from {dataset_path}")
    return tasks

def run_dual_track(dataset: List[Dict[str, Any]], output_path: str) -> List[Dict[str, Any]]:
    """
    Execute the dual-track agent on the dataset.
    
    Args:
        dataset: List of task dictionaries.
        output_path: Path to write the execution logs.
        
    Returns:
        List of execution log entries.
    """
    logger = get_logger()
    paths = get_paths()
    model_config = get_model_config()
    
    # Initialize components
    # Load the SLM model (Phi-3-mini)
    logger.info("Loading Phi-3-mini model...")
    try:
        # Use the monolithic agent as the generator component
        generator_config = MonolithicAgentConfig(
            model_name=model_config.model_name,
            max_tokens=model_config.max_tokens,
            temperature=model_config.temperature
        )
        generator = MonolithicAgent(generator_config)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    # Initialize constraint store and resolver
    constraint_store = ConstraintStore()
    resolver = ConstraintResolver()
    
    # Initialize judge for scoring
    judge = AdaPlanJudge()
    
    results = []
    
    for task in dataset:
        task_id = task.get('task_id', f"task_{len(results)}")
        raw_prompt = task.get('raw_prompt', '')
        progressive_constraints = task.get('progressive_constraints', [])
        constraint_count = task.get('constraint_count', len(progressive_constraints))
        
        logger.info(f"Processing task {task_id} with {constraint_count} constraints")
        
        try:
            # Step 1: Generate initial plan using the generator
            task_context = TaskContext(
                task_id=task_id,
                raw_prompt=raw_prompt,
                constraints=progressive_constraints,
                constraint_count=constraint_count
            )
            
            # Generate plan
            generated_plan = generator.generate_plan(task_context)
            
            # Step 2: Check for violations using constraint store and resolver
            violations = []
            violation_status = None
            violation_reason = None
            
            # Add all constraints to the store
            for constraint_text in progressive_constraints:
                constraint_store.add_constraint(task_id, constraint_text)
            
            # Check for violations in the generated plan
            # The resolver checks the plan against constraints
            resolution_logs = resolver.check_plan(task_id, generated_plan, progressive_constraints)
            
            if resolution_logs:
                # Process resolution logs to determine violation status
                for log in resolution_logs:
                    if log.get('is_violation'):
                        violations.append(log)
                        violation_reason = log.get('reason', 'Constraint violation detected')
                        
                        # Determine violation status based on FR-008 and FR-009
                        if log.get('status') == 'false_negative':
                            violation_status = 'false_negative'
                        elif log.get('status') == 'implicit_unverified':
                            violation_status = 'implicit_unverified'
                        else:
                            violation_status = 'explicit_violation'
            
            # Step 3: Score the plan using the judge
            try:
                final_score = judge.score_task(task_id, generated_plan, progressive_constraints)
            except Exception as e:
                logger.warning(f"Failed to score task {task_id}: {e}")
                final_score = 0.0
            
            # Step 4: Create execution log entry
            log_entry = {
                'task_id': task_id,
                'constraint_count': constraint_count,
                'generated_plan': generated_plan,
                'violation_boolean': len(violations) > 0,
                'violation_reason': violation_reason,
                'violation_status': violation_status,
                'final_score': float(final_score)
            }
            
            results.append(log_entry)
            logger.info(f"Completed task {task_id}: violation={log_entry['violation_boolean']}, score={final_score}")
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            # Create error log entry
            error_log = {
                'task_id': task_id,
                'constraint_count': constraint_count,
                'generated_plan': '',
                'violation_boolean': False,
                'violation_reason': f'Execution error: {str(e)}',
                'violation_status': None,
                'final_score': 0.0
            }
            results.append(error_log)
    
    # Write results to output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for entry in results:
            f.write(json.dumps(entry) + '\n')
    
    logger.info(f"Wrote {len(results)} execution logs to {output_path}")
    return results

def main():
    """Main entry point for dual-track runner."""
    parser = argparse.ArgumentParser(description='Execute dual-track agent on filtered dataset')
    parser.add_argument('--dataset', type=str, default='data/processed/filtered_tasks.csv',
                      help='Path to filtered tasks dataset')
    parser.add_argument('--output', type=str, default='data/processed/dual_track_logs.json',
                      help='Path to output execution logs')
    
    args = parser.parse_args()
    
    logger = get_logger()
    logger.info("Starting dual-track execution...")
    
    try:
        # Load dataset
        dataset = load_filtered_tasks_dataset(args.dataset)
        
        if not dataset:
            logger.error("No tasks found in dataset")
            sys.exit(1)
        
        # Execute dual-track
        run_dual_track(dataset, args.output)
        
        logger.info("Dual-track execution completed successfully")
        
    except Exception as e:
        logger.error(f"Dual-track execution failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()