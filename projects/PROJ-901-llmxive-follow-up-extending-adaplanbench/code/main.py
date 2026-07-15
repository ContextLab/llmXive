import os
import sys
import time
import resource
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# Local imports based on API surface
from config import Paths, set_all_seeds, ResourceLimits, ModelConfig
from dataset.loader import load_adaplanbench, filter_progressive_constraints, save_filtered_dataset
from agent.monolithic import MonolithicAgent, MonolithicAgentConfig
from agent.dual_track import DualTrackAgent, run_dual_track_experiment
from agent.base import ExecutionResult, TaskContext

# Ensure paths are initialized
if not hasattr(Paths, 'BASE_DIR'):
    # Fallback if config hasn't been fully loaded in this context, 
    # though typically config.py handles this.
    BASE_DIR = Path(__file__).resolve().parent.parent
    Paths.BASE_DIR = BASE_DIR
    Paths.RAW_DATA_DIR = BASE_DIR / "data" / "raw"
    Paths.PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
    Paths.CODE_DIR = BASE_DIR / "code"

class ResourceMonitor:
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self.start_time: Optional[float] = None
        self.start_rss: Optional[int] = None

    def start(self):
        self.start_time = time.time()
        self.start_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    def check(self):
        if not self.start_time:
            return
        
        current_time = time.time()
        current_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Convert KB to MB (ru_maxrss is in KB on Linux/macOS)
        current_mb = current_rss / 1024
        
        if self.limits.max_memory_mb and current_mb > self.limits.max_memory_mb:
            raise MemoryError(
                f"Memory limit exceeded: {current_mb:.2f} MB > {self.limits.max_memory_mb} MB"
            )
        
        elapsed = current_time - self.start_time
        if self.limits.max_time_seconds and elapsed > self.limits.max_time_seconds:
            raise TimeoutError(
                f"Time limit exceeded: {elapsed:.2f} s > {self.limits.max_time_seconds} s"
            )

def run_dataset_preparation():
    """
    Executes T012-T015: Load, filter, and save the progressive constraint subset.
    """
    print(">>> Starting Dataset Preparation (T012-T015)...")
    monitor = ResourceMonitor()
    monitor.start()

    try:
        # Load raw dataset (T012)
        print("Loading AdaPlanBench dataset...")
        raw_data = load_adaplanbench()
        
        # Filter for progressive constraints >= 5 (T013)
        print("Filtering tasks with >= 5 progressive constraints...")
        filtered_data = filter_progressive_constraints(raw_data, min_constraints=5)
        
        # Add constraint_count metadata (T014)
        print("Adding constraint_count column...")
        # Assuming filter_progressive_constraints returns a list of dicts or similar structure
        # We ensure the column exists by counting the 'progressive_constraints' list if present
        for item in filtered_data:
            if 'progressive_constraints' in item:
                item['constraint_count'] = len(item['progressive_constraints'])
            else:
                item['constraint_count'] = 0
        
        # Save to CSV (T014)
        output_path = Paths.PROCESSED_DATA_DIR / "filtered_tasks.csv"
        print(f"Saving filtered dataset to {output_path}...")
        save_filtered_dataset(filtered_data, output_path)
        
        # Validate subset (T015)
        print("Validating subset...")
        # Assuming validate_subset is a function that runs checks
        # We call it here to ensure the data is consistent
        from dataset.validate_subset import validate_subset
        validation_results = validate_subset(output_path)
        
        if validation_results.get('valid', False):
            print("Dataset preparation complete and validated.")
        else:
            print("WARNING: Dataset validation returned non-critical issues.")
            
    finally:
        monitor.check()
    
    print(">>> Dataset Preparation Finished.\n")

def run_agent_execution():
    """
    Executes T023-T024: Run both Monolithic and Dual-Track agents on filtered data.
    Generates data/processed/execution_traces.csv.
    """
    print(">>> Starting Agent Execution (T023-T024)...")
    monitor = ResourceMonitor()
    monitor.start()

    input_path = Paths.PROCESSED_DATA_DIR / "filtered_tasks.csv"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Filtered dataset not found at {input_path}. "
            "Run dataset preparation first."
        )

    # Load filtered tasks
    tasks = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse constraint_count if it's a string representation of a list or int
            try:
                row['constraint_count'] = int(row.get('constraint_count', 0))
            except (ValueError, TypeError):
                row['constraint_count'] = 0
            tasks.append(row)

    print(f"Loaded {len(tasks)} tasks for execution.")

    # Configuration
    # Using a CPU-tractable model as per spec
    model_config = ModelConfig(
        model_name="microsoft/phi-2", # Example SLM, adjust if specific small model required
        device="cpu",
        precision="float32"
    )
    
    monolithic_config = MonolithicAgentConfig(
        model_config=model_config,
        temperature=0.0
    )

    results = []
    output_path = Paths.PROCESSED_DATA_DIR / "execution_traces.csv"
    
    # Initialize agents
    print("Initializing Monolithic Agent...")
    monolithic_agent = MonolithicAgent(monolithic_config)
    
    print("Initializing Dual-Track Agent...")
    dual_track_agent = DualTrackAgent()

    for idx, task in enumerate(tasks):
        monitor.check()
        task_id = task.get('id', f"task_{idx}")
        print(f"Processing {idx+1}/{len(tasks)}: {task_id}")

        # 1. Run Monolithic
        print(f"  -> Running Monolithic on {task_id}...")
        try:
            monolithic_result = monolithic_agent.execute(task)
            monolithic_violation = monolithic_result.violations > 0
            monolithic_score = monolithic_result.final_score
        except Exception as e:
            print(f"    ERROR in Monolithic: {e}")
            monolithic_violation = True
            monolithic_score = 0.0
            monolithic_result = ExecutionResult(
                plan=[], violations=1, final_score=0.0, logs=["Execution failed"]
            )

        # 2. Run Dual-Track
        print(f"  -> Running Dual-Track on {task_id}...")
        try:
            dual_track_result = dual_track_agent.execute(task)
            dual_violation = dual_track_result.violations > 0
            dual_score = dual_track_result.final_score
        except Exception as e:
            print(f"    ERROR in Dual-Track: {e}")
            dual_violation = True
            dual_score = 0.0
            dual_track_result = ExecutionResult(
                plan=[], violations=1, final_score=0.0, logs=["Execution failed"]
            )

        # Record results
        results.append({
            "task_id": task_id,
            "constraint_count": task['constraint_count'],
            "architecture": "monolithic",
            "violation": monolithic_violation,
            "score": monolithic_score,
            "execution_time_ms": 0, # Placeholder if not measured
            "log_summary": str(monolithic_result.logs[:5])
        })
        
        results.append({
            "task_id": task_id,
            "constraint_count": task['constraint_count'],
            "architecture": "dual_track",
            "violation": dual_violation,
            "score": dual_score,
            "execution_time_ms": 0,
            "log_summary": str(dual_track_result.logs[:5])
        })

    # Write to CSV
    print(f"Writing execution traces to {output_path}...")
    if results:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"Executed {len(tasks)} tasks. Total traces: {len(results)}")
    print(">>> Agent Execution Finished.\n")

def run_statistical_analysis():
    """
    Placeholder for T027-T032: GLMM and statistical analysis.
    """
    print(">>> Starting Statistical Analysis (T027-T032)...")
    # This will be implemented in Phase 5
    print(">>> Statistical Analysis Placeholder.\n")

def run_all_tasks():
    """
    Orchestrates the full pipeline: Dataset Prep -> Agent Execution -> Analysis.
    """
    print("="*60)
    print("LLMxive Automated Science Pipeline")
    print("="*60)
    
    start_time = time.time()
    
    try:
        run_dataset_preparation()
        run_agent_execution()
        run_statistical_analysis()
        
        elapsed = time.time() - start_time
        print(f"Pipeline completed in {elapsed:.2f} seconds.")
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

def main():
    """
    Entry point for the script.
    Usage: python code/main.py
    """
    # Set seeds for reproducibility
    set_all_seeds(42)
    
    # Run the full pipeline
    run_all_tasks()

if __name__ == "__main__":
    main()