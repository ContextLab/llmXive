import argparse
import json
import os
import sys
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing API surface
from generators.synthetic_workflow import SyntheticWorkflowGenerator, main as gen_main
from engines.oracle_policy import OraclePolicyEngine, main as oracle_main
from engines.full_context import FullContextEngine, main as full_main
from utils.state_manager import update_state_with_artifacts, compute_directory_hashes, load_state, save_state

def ensure_directories(base_path: Path) -> None:
    """Ensure all required data directories exist."""
    dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "state" / "projects"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def generate_workflows(
    base_path: Path,
    count: int,
    seed: int,
    output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Generate synthetic workflows and save them to data/raw/.
    
    Args:
        base_path: Project root path
        count: Number of workflows to generate
        seed: Random seed for determinism
        output_dir: Optional override for output directory
        
    Returns:
        List of generated workflow metadata dicts
    """
    if output_dir is None:
        output_dir = base_path / "data" / "raw"
        
    generator = SyntheticWorkflowGenerator(seed=seed)
    workflows = generator.generate_batch(count=count)
    
    saved_files = []
    for i, wf in enumerate(workflows):
        filename = f"workflow_{i:04d}.json"
        filepath = output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(wf, f, indent=2)
        saved_files.append({
            "id": wf.get("id"),
            "depth": wf.get("depth"),
            "complexity": wf.get("complexity"),
            "file": str(filepath.relative_to(base_path))
        })
        
    return saved_files

def validate_with_oracle(
    base_path: Path,
    workflow_files: List[Path],
    output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Validate workflows using the Oracle Policy Engine.
    
    Args:
        base_path: Project root path
        workflow_files: List of workflow file paths to validate
        output_dir: Optional override for output directory
        
    Returns:
        List of validation results
    """
    if output_dir is None:
        output_dir = base_path / "data" / "raw" / "oracle_logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    oracle = OraclePolicyEngine()
    results = []
    
    for wf_file in workflow_files:
        with open(wf_file, 'r') as f:
            workflow = json.load(f)
            
        validation = oracle.validate_workflow(workflow)
        
        log_filename = f"oracle_{wf_file.stem}.json"
        log_path = output_dir / log_filename
        with open(log_path, 'w') as f:
            json.dump(validation, f, indent=2)
            
        results.append({
            "workflow_id": workflow.get("id"),
            "is_valid": validation.get("is_valid"),
            "violations": validation.get("violations", []),
            "log_file": str(log_path.relative_to(base_path))
        })
        
    return results

def execute_full_context(
    base_path: Path,
    workflow_files: List[Path],
    oracle_logs_dir: Path,
    output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Execute workflows with full context and record execution logs.
    
    Args:
        base_path: Project root path
        workflow_files: List of workflow file paths to execute
        oracle_logs_dir: Directory containing oracle validation logs
        output_dir: Optional override for output directory
        
    Returns:
        List of execution log metadata
    """
    if output_dir is None:
        output_dir = base_path / "data" / "processed" / "full_context_logs"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    engine = FullContextEngine()
    results = []
    
    for wf_file in workflow_files:
        with open(wf_file, 'r') as f:
            workflow = json.load(f)
            
        # Load corresponding oracle log if exists
        oracle_log_path = oracle_logs_dir / f"oracle_{wf_file.stem}.json"
        oracle_log = None
        if oracle_log_path.exists():
            with open(oracle_log_path, 'r') as f:
                oracle_log = json.load(f)
        
        execution = engine.execute(workflow, oracle_log=oracle_log)
        
        log_filename = f"exec_{wf_file.stem}.json"
        log_path = output_dir / log_filename
        with open(log_path, 'w') as f:
            json.dump(execution, f, indent=2)
            
        results.append({
            "workflow_id": workflow.get("id"),
            "status": execution.get("status"),
            "steps_executed": execution.get("steps_executed", 0),
            "policy_violations": execution.get("policy_violations", []),
            "log_file": str(log_path.relative_to(base_path))
        })
        
    return results

def main():
    """Main orchestrator entry point."""
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument(
        "--action",
        choices=["generate", "validate", "execute", "full"],
        default="full",
        help="Action to perform: generate workflows, validate with oracle, execute, or full pipeline"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of workflows to generate (default: 100)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation (default: 42)"
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=".",
        help="Project base path (default: current directory)"
    )
    
    args = parser.parse_args()
    base_path = Path(args.base_path).resolve()
    
    print(f"Starting llmXive orchestrator at {base_path}")
    print(f"Action: {args.action}, Count: {args.count}, Seed: {args.seed}")
    
    ensure_directories(base_path)
    
    workflow_files = []
    if args.action in ["generate", "full"]:
        print("Generating workflows...")
        workflows = generate_workflows(base_path, args.count, args.seed)
        workflow_files = [base_path / "data" / "raw" / f["file"] for f in workflows]
        print(f"Generated {len(workflows)} workflows")
        
        # Save generation metadata
        meta_path = base_path / "data" / "raw" / "generation_metadata.json"
        with open(meta_path, 'w') as f:
            json.dump({
                "count": args.count,
                "seed": args.seed,
                "workflows": workflows
            }, f, indent=2)
        print(f"Saved generation metadata to {meta_path}")
    
    if args.action in ["validate", "full"]:
        print("Validating with Oracle...")
        if not workflow_files:
            # If we didn't generate, try to find existing files
            raw_dir = base_path / "data" / "raw"
            workflow_files = list(raw_dir.glob("workflow_*.json"))
            if not workflow_files:
                print("No workflows found to validate. Run generation first.")
                return
        
        oracle_results = validate_with_oracle(base_path, workflow_files)
        print(f"Validated {len(oracle_results)} workflows")
        
        # Save validation summary
        summary_path = base_path / "data" / "raw" / "oracle_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(oracle_results, f, indent=2)
        print(f"Saved oracle summary to {summary_path}")
    
    if args.action in ["execute", "full"]:
        print("Executing with Full Context...")
        raw_dir = base_path / "data" / "raw"
        if not workflow_files:
            workflow_files = list(raw_dir.glob("workflow_*.json"))
        
        oracle_logs_dir = base_path / "data" / "raw" / "oracle_logs"
        if not oracle_logs_dir.exists():
            print("Oracle logs not found. Run validation first.")
            return
            
        exec_results = execute_full_context(base_path, workflow_files, oracle_logs_dir)
        print(f"Executed {len(exec_results)} workflows")
        
        # Save execution summary
        exec_summary_path = base_path / "data" / "processed" / "full_execution_summary.json"
        with open(exec_summary_path, 'w') as f:
            json.dump(exec_results, f, indent=2)
        print(f"Saved execution summary to {exec_summary_path}")
    
    # Update state registry with artifact hashes
    print("Updating state registry...")
    try:
        state = load_state(base_path / "state" / "projects" / "PROJ-866-llmxive-follow-up-extending-foundation-p.yaml")
        updated_state = update_state_with_artifacts(state, base_path)
        save_state(updated_state, base_path / "state" / "projects" / "PROJ-866-llmxive-follow-up-extending-foundation-p.yaml")
        print("State registry updated successfully")
    except Exception as e:
        print(f"Warning: Could not update state registry: {e}")
    
    print("Orchestrator complete.")

if __name__ == "__main__":
    main()