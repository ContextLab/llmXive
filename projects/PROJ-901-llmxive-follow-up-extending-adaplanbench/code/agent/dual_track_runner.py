import os
import sys
import json
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_model_config, get_paths, ProjectLogger, ensure_directories
from agent.base import TaskContext, ExecutionResult, ViolationType
from agent.monolithic import MonolithicAgent, MonolithicAgentConfig
from agent.constraint_store import ConstraintStore
from agent.resolver import ConstraintResolver, ResolutionLog
from agent.judges import AdaPlanJudge

logger = ProjectLogger.get_logger("dual_track_runner")

def load_filtered_tasks_dataset(input_path: str) -> List[Dict[str, Any]]:
    """
    Load the filtered tasks dataset from the specified CSV path.
    Expected columns: task_id, raw_prompt, progressive_constraints, constraint_count
    """
    tasks = []
    logger.info(f"Loading filtered tasks from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered tasks file not found: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task = {
                'task_id': row['task_id'],
                'raw_prompt': row['raw_prompt'],
                'constraint_count': int(row['constraint_count']),
                'progressive_constraints': row['progressive_constraints']
            }
            # Parse the list string if it's stored as a string representation
            if isinstance(task['progressive_constraints'], str):
                # Handle potential string representation of list
                try:
                    # Simple evaluation for list of strings
                    if task['progressive_constraints'].startswith('['):
                        task['progressive_constraints'] = eval(task['progressive_constraints'])
                    else:
                        task['progressive_constraints'] = [task['progressive_constraints']]
                except:
                    task['progressive_constraints'] = [task['progressive_constraints']]
            
            tasks.append(task)
    
    logger.info(f"Loaded {len(tasks)} tasks")
    return tasks

def run_dual_track(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Execute the dual-track agent on the provided dataset.
    
    Logic:
    1. Load Model: Load the Phi-3-mini model (from cache or download).
    2. Execute: Invoke generator, constraint store, and resolver for each task.
    3. Log: Integrate resolver's output (violation, false_negative, implicit_unverified)
       into the execution trace.
    4. Write: Return results conforming to execution-log.schema.yaml.
    
    Args:
        dataset: List of task dictionaries from filtered_tasks.csv.
        
    Returns:
        List of execution log dictionaries.
    """
    logger.info("Initializing Dual-Track Agent execution")
    
    # Load configuration and model
    model_config = get_model_config()
    paths = get_paths()
    ensure_directories()
    
    # Initialize components
    # The MonolithicAgent here acts as the SLM Generator for the dual-track architecture
    generator = MonolithicAgent(model_config)
    
    # Constraint store for deterministic constraint tracking
    constraint_store = ConstraintStore()
    
    # Resolver for checking violations
    resolver = ConstraintResolver()
    
    # Judge for scoring (if available, otherwise fallback logic)
    try:
        judge = AdaPlanJudge()
    except Exception as e:
        logger.warning(f"Judge initialization failed: {e}. Using fallback scoring.")
        judge = None

    results = []

    for task in dataset:
        task_id = task['task_id']
        raw_prompt = task['raw_prompt']
        constraint_count = task['constraint_count']
        progressive_constraints = task.get('progressive_constraints', [])

        logger.info(f"Processing task {task_id} with {constraint_count} constraints")

        # 1. Generate Plan (SLM Generator)
        # We pass the prompt and the known constraints to the generator to simulate
        # the dual-track interaction where the generator might not "see" all constraints
        # but the store does. For this implementation, we generate a plan based on the prompt.
        try:
            plan = generator.generate(raw_prompt)
        except Exception as e:
            logger.error(f"Generation failed for {task_id}: {e}")
            plan = "Generation failed due to error."

        # 2. Check Constraints & Resolve Violations
        # We simulate the progressive nature by checking against the full list
        # but the resolver handles the logic of detection and status.
        
        violation_status = None
        violation_reason = None
        violation_boolean = False
        
        # Check each constraint
        for constraint_text in progressive_constraints:
            # Add to store
            constraint_store.add_constraint(task_id, constraint_text)
            
            # Check for violation in the generated plan
            # The resolver checks if the plan violates the constraint
            resolution = resolver.check_and_resolve(task_id, plan, constraint_text)
            
            if resolution.violation_detected:
                violation_boolean = True
                violation_reason = resolution.reason
                violation_status = resolution.status # "violation", "false_negative", "implicit_unverified"
                break # Stop at first violation for this log entry

        # 3. Score (Final Score)
        final_score = 0.0
        if judge:
            try:
                # Score based on plan adherence to constraints
                score_result = judge.score(task_id, plan, progressive_constraints)
                final_score = float(score_result)
            except Exception as e:
                logger.warning(f"Scoring failed for {task_id}: {e}")
                final_score = 0.0
        else:
            # Fallback scoring logic if judge is missing
            # Simple heuristic: if no violation, score 1.0, else 0.0
            final_score = 0.0 if violation_boolean else 1.0

        # Construct log entry conforming to execution-log.schema.yaml
        log_entry = {
            "task_id": task_id,
            "constraint_count": constraint_count,
            "generated_plan": plan,
            "violation_boolean": violation_boolean,
            "violation_reason": violation_reason,
            "violation_status": violation_status, # "implicit_unverified", "false_negative", or null
            "final_score": final_score
        }
        
        results.append(log_entry)

    logger.info(f"Dual-track execution complete. Generated {len(results)} logs.")
    return results

def main():
    """
    CLI entry point for running the dual-track agent.
    """
    parser = argparse.ArgumentParser(description="Run Dual-Track Agent on filtered dataset")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/filtered_tasks.csv",
        help="Path to the filtered tasks CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/dual_track_logs.json",
        help="Path to write the output JSON logs"
    )
    
    args = parser.parse_args()
    
    try:
        # Load dataset
        dataset = load_filtered_tasks_dataset(args.input)
        
        if not dataset:
            logger.error("Dataset is empty. Cannot proceed.")
            sys.exit(1)
        
        # Execute
        results = run_dual_track(dataset)
        
        # Write output
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results written to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
