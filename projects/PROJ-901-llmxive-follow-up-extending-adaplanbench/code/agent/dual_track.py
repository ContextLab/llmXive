"""
Dual-Track Agent Orchestration Module.

Implements the Dual-Track architecture:
1. Generator (SLM) proposes a plan.
2. Constraint Store (Deterministic) holds active constraints.
3. Resolver (Rule-based) checks for violations and forces revisions.

Logs "false_negative" if intent parsing fails (FR-008).
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# Import from local project modules
from agent.base import ViolationType, ExecutionResult, TaskContext
from agent.constraint_store import Constraint, ConstraintStore
from agent.resolver import ConstraintResolver, ResolutionLog
from agent.monolithic import MonolithicAgent, MonolithicAgentConfig
from config import get_dataset_config, get_model_config, get_paths

# Ensure paths are set up if not already
try:
    from config import ensure_directories
    ensure_directories()
except Exception:
    pass

class DualTrackAgent:
    """
    Orchestrates the generator, store, and resolver for the dual-track architecture.
    """
    def __init__(self, model_config: MonolithicAgentConfig = None):
        self.model_config = model_config or MonolithicAgentConfig()
        self.generator = MonolithicAgent(self.model_config)
        self.store = ConstraintStore()
        self.resolver = ConstraintResolver()
        
    def process_task(self, task: Dict[str, Any]) -> ExecutionResult:
        """
        Process a single task through the dual-track pipeline.
        
        Args:
            task: Dictionary containing 'task_id', 'raw_prompt', 'progressive_constraints', etc.
            
        Returns:
            ExecutionResult object.
        """
        task_id = task.get('task_id', str(uuid.uuid4()))
        raw_prompt = task.get('raw_prompt', '')
        progressive_constraints = task.get('progressive_constraints', [])
        
        # 1. Initialize Context
        context = TaskContext(
            task_id=task_id,
            prompt=raw_prompt,
            constraints=progressive_constraints,
            timestamp=datetime.now()
        )
        
        # 2. Load Constraints into Store
        for c_text in progressive_constraints:
            self.store.add_constraint(task_id, c_text)
        
        # 3. Generate Initial Plan
        try:
            initial_plan = self.generator.generate_plan(context)
        except Exception as e:
            # Intent parsing failure -> Log false_negative
            return ExecutionResult(
                task_id=task_id,
                success=False,
                plan="",
                violation_status="false_negative",
                violation_reason=f"Generator failed: {str(e)}",
                final_score=0.0
            )
        
        # 4. Check for Violations and Resolve
        current_plan = initial_plan
        violation_log = []
        final_violation_status = None
        final_violation_reason = None
        is_violated = False
        
        # Check against all constraints
        active_constraints = self.store.get_active_constraints(task_id)
        
        for constraint in active_constraints:
            violation = self.resolver.check_violation(task_id, current_plan, constraint)
            
            if violation:
                is_violated = True
                final_violation_status = violation.get('status', 'violation')
                final_violation_reason = violation.get('reason', 'Unknown constraint violation')
                
                # FR-003: Force Revision
                # Attempt to generate a corrected plan
                corrected_plan = self.resolver.force_revision(
                    task_id, 
                    current_plan, 
                    violation, 
                    active_constraints
                )
                
                if corrected_plan:
                    current_plan = corrected_plan
                    # Re-check the corrected plan against remaining constraints
                    # (Simplified: in a full loop we'd re-verify all, but here we log the fix attempt)
                else:
                    # Could not fix
                    pass
                
                violation_log.append(violation)
            else:
                # Check for implicit/unverified constraints (FR-009)
                # If resolver couldn't match explicitly but we suspect a constraint exists
                # The resolver returns None if no match. We log "implicit_unverified" if
                # the constraint text was non-empty but no specific rule matched.
                if constraint.text and not self.resolver.has_explicit_rule(constraint.text):
                    # Log as implicit_unverified (per T024/T026c requirements)
                    # Note: This does NOT set is_violated=True for the primary metric,
                    # but we record it in the log.
                    log_entry = {
                        "task_id": task_id,
                        "constraint": constraint.text,
                        "status": "implicit_unverified",
                        "reason": "No explicit rule matched for constraint"
                    }
                    violation_log.append(log_entry)
                    # We do NOT set final_violation_status to 'implicit_unverified' 
                    # if a real violation was already found, to preserve the primary metric.
                    # If no real violation found, we might flag it, but per FR-009 
                    # we exclude these from the primary violation rate.
                    if not is_violated:
                        final_violation_status = "implicit_unverified"
                        final_violation_reason = "Unverified implicit constraint detected"

        # 5. Calculate Final Score
        # Simple heuristic: 1.0 if no violation, 0.0 if violation, partial if corrected?
        # For now, binary based on final state
        final_score = 0.0 if is_violated else 1.0
        
        # If we had an implicit_unverified but no hard violation, score might still be 1.0
        # but the status reflects the ambiguity.
        if final_violation_status == "implicit_unverified" and not is_violated:
            final_score = 1.0 # Still counts as success for the primary metric per FR-009
        
        return ExecutionResult(
            task_id=task_id,
            success=not is_violated,
            plan=current_plan,
            violation_status=final_violation_status,
            violation_reason=final_violation_reason,
            final_score=final_score,
            logs=violation_log
        )

def run_dual_track_experiment(
    input_path: str, 
    output_path: str
) -> None:
    """
    Runs the dual-track agent on a filtered dataset and writes logs to JSON.
    
    Args:
        input_path: Path to the filtered_tasks.csv
        output_path: Path to write dual_track_logs.json
    """
    paths = get_paths()
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    agent = DualTrackAgent()
    results = []
    
    # Load CSV
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        tasks = list(reader)
        
    if not tasks:
        print("No tasks found in input file.")
        return

    print(f"Processing {len(tasks)} tasks with Dual-Track Agent...")
    
    for i, task in enumerate(tasks):
        # Ensure constraint lists are parsed if they are string representations of lists
        pc = task.get('progressive_constraints', '[]')
        if isinstance(pc, str):
            try:
                import ast
                task['progressive_constraints'] = ast.literal_eval(pc)
            except:
                task['progressive_constraints'] = []
                
        result = agent.process_task(task)
        
        # Convert result to dict for JSON serialization
        log_entry = {
            "task_id": result.task_id,
            "constraint_count": len(task.get('progressive_constraints', [])),
            "generated_plan": result.plan,
            "violation_boolean": not result.success,
            "violation_reason": result.violation_reason,
            "violation_status": result.violation_status,
            "final_score": result.final_score,
            "detailed_logs": result.logs
        }
        results.append(log_entry)
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(tasks)} tasks.")
            
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
        
    print(f"Dual-Track execution complete. Results written to {output_path}")

def main():
    """CLI entry point for dual-track execution."""
    import argparse
    parser = argparse.ArgumentParser(description="Run Dual-Track Agent Experiment")
    parser.add_argument("--input", type=str, required=True, help="Path to filtered_tasks.csv")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON logs")
    args = parser.parse_args()
    
    run_dual_track_experiment(args.input, args.output)

if __name__ == "__main__":
    main()