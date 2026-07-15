import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Project imports
from config import Paths
from agent.base import ViolationType, ExecutionResult, TaskContext, BaseAgent
from agent.constraint_store import Constraint, ConstraintStore
from agent.resolver import ConstraintResolver, ResolutionLog
from agent.monolithic import MonolithicAgent

# Local imports relative to code/
from dataset.loader import load_adaplanbench, filter_progressive_constraints

class DualTrackAgent(BaseAgent):
    """
    Orchestrates the dual-track architecture:
    1. Generator (SLM) proposes a plan.
    2. ConstraintStore tracks active constraints.
    3. Resolver (Deterministic) checks for violations and corrects.

    Logs "false_negative" if intent parsing fails (FR-008).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.store = ConstraintStore()
        self.resolver = ConstraintResolver()
        # Using MonolithicAgent as the SLM Generator for this implementation
        self.generator = MonolithicAgent()
        self.execution_logs: List[Dict[str, Any]] = []

    def _parse_intent(self, task_description: str) -> Optional[Dict[str, Any]]:
        """
        Parses the task description to extract intent.
        Returns None if parsing fails (triggers false_negative log).
        """
        # Simple heuristic: if description is empty or too short, parsing fails.
        # In a real scenario, this might call an LLM to extract structured intent.
        if not task_description or len(task_description.strip()) < 5:
            return None
        
        # Basic extraction: assume the whole description is the intent for now
        # or split by specific keywords if the dataset format dictates.
        # For AdaPlanBench, we treat the 'instruction' as the intent.
        return {
            "raw_intent": task_description,
            "parsed_successfully": True
        }

    def _log_false_negative(self, task_id: str, reason: str) -> None:
        """Logs a false_negative event as per FR-008."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "event_type": "false_negative",
            "reason": reason,
            "architecture": "dual_track"
        }
        self.execution_logs.append(log_entry)

    def _log_violation(self, task_id: str, constraint: Constraint, resolution: Optional[ResolutionLog]) -> None:
        """Logs a constraint violation event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "event_type": "violation_detected",
            "constraint_id": constraint.id,
            "constraint_text": constraint.text,
            "resolution_status": "resolved" if resolution else "unresolved",
            "resolution_details": resolution.to_dict() if resolution else None,
            "architecture": "dual_track"
        }
        self.execution_logs.append(log_entry)

    def execute(self, task: Dict[str, Any]) -> ExecutionResult:
        """
        Executes the dual-track logic for a single task.
        
        Args:
            task: Dictionary containing 'id', 'instruction', 'constraints', etc.
        
        Returns:
            ExecutionResult with status and metrics.
        """
        task_id = task.get('id', 'unknown')
        instruction = task.get('instruction', '')
        constraints_data = task.get('constraints', [])
        
        # 1. Parse Intent
        intent = self._parse_intent(instruction)
        if not intent:
            self._log_false_negative(task_id, "Intent parsing failed: empty or invalid instruction")
            return ExecutionResult(
                task_id=task_id,
                status="failed",
                violation_count=0,
                final_score=0.0,
                log=self.execution_logs[-1]
            )

        # 2. Load Constraints into Store
        # The dataset provides constraints. We load them into the store.
        # Assuming constraints_data is a list of dicts or strings.
        for idx, c_data in enumerate(constraints_data):
            if isinstance(c_data, dict):
                text = c_data.get('text', c_data.get('constraint', ''))
            else:
                text = str(c_data)
            
            if text:
                self.store.add_constraint(text, source="dataset")

        # 3. Generator (SLM) produces a plan
        # We simulate the generator step. In a full run, this calls the LLM.
        # For this implementation, we assume the generator produces a plan string.
        # If the generator fails, we handle it similarly to intent parsing.
        try:
            generated_plan = self.generator.generate_plan(instruction, self.store.get_active_constraints())
        except Exception as e:
            self._log_false_negative(task_id, f"Generator failed: {str(e)}")
            return ExecutionResult(
                task_id=task_id,
                status="failed",
                violation_count=0,
                final_score=0.0,
                log=self.execution_logs[-1]
            )

        # 4. Resolver checks for violations
        violations_found = 0
        resolution_attempts = []
        
        # Check the generated plan against the store
        # The resolver iterates over active constraints and checks the plan.
        active_constraints = self.store.get_active_constraints()
        
        for constraint in active_constraints:
            resolution = self.resolver.check_and_resolve(generated_plan, constraint)
            
            if resolution and resolution.is_violation:
                violations_found += 1
                self._log_violation(task_id, constraint, resolution)
                resolution_attempts.append(resolution.to_dict())
            elif resolution and not resolution.is_violation:
                # Constraint satisfied or not applicable
                pass

        # 5. Compute Final Score
        # Simple heuristic: 1.0 if no violations, reduced by violation count
        total_constraints = len(active_constraints)
        if total_constraints == 0:
            final_score = 1.0
        else:
            final_score = max(0.0, 1.0 - (violations_found / total_constraints))

        return ExecutionResult(
            task_id=task_id,
            status="completed",
            violation_count=violations_found,
            final_score=final_score,
            log=self.execution_logs
        )

def run_dual_track_experiment():
    """
    Main entry point to run the dual-track agent on the filtered dataset.
    Reads from data/processed/filtered_tasks.csv and writes to data/processed/execution_traces.csv
    """
    paths = Paths()
    input_path = paths.processed_dir / "filtered_tasks.csv"
    output_path = paths.processed_dir / "execution_traces.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run dataset preparation first.")

    print(f"Loading tasks from {input_path}...")
    df = load_adaplanbench() # Reusing loader logic or reading CSV directly
    # Since we need to read the CSV specifically created by T014
    import pandas as pd
    tasks_df = pd.read_csv(input_path)

    agent = DualTrackAgent()
    results = []

    print(f"Processing {len(tasks_df)} tasks...")
    for idx, row in tasks_df.iterrows():
        task_dict = row.to_dict()
        # Ensure constraints are parsed if they are stringified lists
        if isinstance(task_dict.get('constraints'), str):
            import ast
            try:
                task_dict['constraints'] = ast.literal_eval(task_dict['constraints'])
            except:
                task_dict['constraints'] = []

        result = agent.execute(task_dict)
        
        # Flatten result for CSV
        result_row = {
            "task_id": result.task_id,
            "architecture": "dual_track",
            "constraint_count": task_dict.get('constraint_count', len(task_dict.get('constraints', []))),
            "violation_count": result.violation_count,
            "final_score": result.final_score,
            "status": result.status,
            "timestamp": datetime.now().isoformat()
        }
        results.append(result_row)

        if (idx + 1) % 10 == 0:
            print(f"Processed {idx + 1}/{len(tasks_df)} tasks.")

    print(f"Writing results to {output_path}...")
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)
    print(f"Done. Results saved to {output_path}")

if __name__ == "__main__":
    run_dual_track_experiment()