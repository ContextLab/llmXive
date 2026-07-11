"""
Orchestrator for the llmXive Foundation Protocol pipeline.

This script generates synthetic workflows using the SyntheticWorkflowGenerator,
validates them with the OraclePolicyEngine, executes them with the FullContextEngine,
and saves the raw workflow data to data/raw/.

Usage:
    python code/main.py --num-workflows 500 --output-dir data/raw/
"""

import argparse
import json
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from generators.synthetic_workflow import SyntheticWorkflowGenerator
from engines.oracle_policy import OraclePolicyEngine
from engines.full_context import FullContextEngine


def ensure_directories(output_dir: str) -> None:
    """Ensure the output directory exists."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    
    # Ensure subdirectories exist as per project structure
    (path / "workflows").mkdir(exist_ok=True)
    (path / "logs").mkdir(exist_ok=True)
    

def generate_workflows(
    num_workflows: int,
    output_dir: str,
    seed: int = 42
) -> List[str]:
    """
    Generate synthetic workflows and save them to disk.
    
    Args:
        num_workflows: Number of workflows to generate
        output_dir: Directory to save workflow files
        seed: Random seed for reproducibility
        
    Returns:
        List of paths to generated workflow files
    """
    ensure_directories(output_dir)
    generator = SyntheticWorkflowGenerator(seed=seed)
    workflows_dir = Path(output_dir) / "workflows"
    
    generated_files = []
    
    print(f"Generating {num_workflows} synthetic workflows...")
    
    for i in range(num_workflows):
        workflow = generator.generate()
        filename = f"workflow_{i:04d}.json"
        filepath = workflows_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(workflow, f, indent=2)
        
        generated_files.append(str(filepath))
        
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{num_workflows} workflows")
    
    print(f"Successfully generated {len(generated_files)} workflows.")
    return generated_files


def validate_with_oracle(workflow_paths: List[str], output_dir: str) -> None:
    """
    Validate workflows using the Oracle Policy Engine.
    
    Args:
        workflow_paths: List of paths to workflow files
        output_dir: Directory to save validation logs
    """
    oracle = OraclePolicyEngine()
    logs_dir = Path(output_dir) / "logs"
    
    print("Validating workflows with Oracle Policy Engine...")
    
    for i, path in enumerate(workflow_paths):
        with open(path, 'r') as f:
            workflow = json.load(f)
        
        # Validate the workflow
        is_valid, violations = oracle.validate(workflow)
        
        # Create a validation log
        log_entry = {
            "workflow_id": workflow.get("id", Path(path).stem),
            "is_valid": is_valid,
            "violations": violations,
            "validation_count": len(violations)
        }
        
        log_filename = f"validation_{Path(path).stem}.json"
        log_path = logs_dir / log_filename
        
        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        
        if (i + 1) % 100 == 0:
            print(f"  Validated {i + 1}/{len(workflow_paths)} workflows")
    
    print(f"Validation complete. Logs saved to {logs_dir}")


def execute_full_context(workflow_paths: List[str], output_dir: str) -> None:
    """
    Execute workflows using the Full Context Engine.
    
    Args:
        workflow_paths: List of paths to workflow files
        output_dir: Directory to save execution logs
    """
    engine = FullContextEngine()
    logs_dir = Path(output_dir) / "logs"
    
    print("Executing workflows with Full Context Engine...")
    
    for i, path in enumerate(workflow_paths):
        with open(path, 'r') as f:
            workflow = json.load(f)
        
        # Execute the workflow
        result = engine.execute(workflow)
        
        # Save execution log
        log_filename = f"execution_{Path(path).stem}.json"
        log_path = logs_dir / log_filename
        
        with open(log_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        if (i + 1) % 100 == 0:
            print(f"  Executed {i + 1}/{len(workflow_paths)} workflows")
    
    print(f"Execution complete. Logs saved to {logs_dir}")


def main():
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(
        description="llmXive Foundation Protocol Orchestrator"
    )
    parser.add_argument(
        "--num-workflows",
        type=int,
        default=100,
        help="Number of synthetic workflows to generate (default: 100)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory for generated data (default: data/raw)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run Oracle validation on generated workflows"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run Full Context execution on generated workflows"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory is absolute path
    output_dir = str(Path(args.output_dir).resolve())
    
    print("=" * 60)
    print("llmXive Foundation Protocol Orchestrator")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Number of workflows: {args.num_workflows}")
    print(f"Random seed: {args.seed}")
    print(f"Validation: {'enabled' if args.validate else 'disabled'}")
    print(f"Execution: {'enabled' if args.execute else 'disabled'}")
    print("=" * 60)
    
    # Step 1: Generate workflows
    workflow_paths = generate_workflows(
        num_workflows=args.num_workflows,
        output_dir=output_dir,
        seed=args.seed
    )
    
    # Step 2: Validate with Oracle (if requested)
    if args.validate:
        validate_with_oracle(workflow_paths, output_dir)
    
    # Step 3: Execute with Full Context (if requested)
    if args.execute:
        execute_full_context(workflow_paths, output_dir)
    
    print("=" * 60)
    print("Orchestration complete!")
    print(f"Workflows saved to: {output_dir}/workflows")
    if args.validate or args.execute:
        print(f"Logs saved to: {output_dir}/logs")
    print("=" * 60)

if __name__ == "__main__":
    main()