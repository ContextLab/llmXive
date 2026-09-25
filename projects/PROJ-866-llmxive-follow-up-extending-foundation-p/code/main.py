import argparse
import json
import os
import sys
import random
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generators.synthetic_workflow import SyntheticWorkflowGenerator
from engines.full_context import FullContextEngine
from engines.compressed_context import CompressedContextEngine
from analysis.tradeoff_model import main as analysis_main
from analysis.bonferroni_correction import main as bonferroni_main
from analysis.threshold_detection import main as threshold_main
from utils.finalize_state_registry import main as finalize_state_main

def ensure_directories():
    """Create necessary directories for data storage."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "state/projects",
        "contracts"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def generate_workflows(count: int = 500, seed: int = 42) -> str:
    """Generate synthetic workflows and save to data/raw/workflows.json."""
    output_path = "data/raw/workflows.json"
    generator = SyntheticWorkflowGenerator(seed=seed)
    workflows = generator.generate_workflows(count=count)
    
    with open(output_path, 'w') as f:
        json.dump(workflows, f, indent=2)
    
    print(f"Generated {len(workflows)} workflows to {output_path}")
    return output_path

def validate_with_oracle(workflows_path: str) -> List[Dict]:
    """Run Oracle validation on all workflows."""
    # Oracle validation is typically done during execution
    # This is a placeholder for explicit validation if needed
    return []

def execute_full_context(workflows_path: str) -> str:
    """Execute full context validation and save logs."""
    engine = FullContextEngine()
    output_path = "data/processed/full_context_logs.json"
    
    # Load workflows
    with open(workflows_path, 'r') as f:
        workflows = json.load(f)
    
    logs = []
    for workflow in workflows:
        log = engine.execute(workflow)
        logs.append(log)
    
    with open(output_path, 'w') as f:
        json.dump(logs, f, indent=2)
    
    print(f"Saved full context logs to {output_path}")
    return output_path

def execute_compressed_context(workflows_path: str, depths: List[int] = None) -> str:
    """Execute compressed context variants and save logs."""
    if depths is None:
        depths = list(range(1, 21))
    
    engine = CompressedContextEngine()
    output_path = "data/processed/compressed_context_logs.json"
    
    # Load workflows
    with open(workflows_path, 'r') as f:
        workflows = json.load(f)
    
    all_logs = []
    for workflow in workflows:
        for depth in depths:
            log = engine.execute(workflow, depth=depth)
            all_logs.append(log)
    
    with open(output_path, 'w') as f:
        json.dump(all_logs, f, indent=2)
    
    print(f"Saved compressed context logs to {output_path}")
    return output_path

def run_full_pipeline(generate_count: int = 500, seed: int = 42):
    """Run the complete pipeline: Generate -> Full Exec -> Compressed Exec -> Analyze."""
    ensure_directories()
    
    print("=== Phase 1: Generating Workflows ===")
    workflows_path = generate_workflows(count=generate_count, seed=seed)
    
    print("\n=== Phase 2: Full Context Execution ===")
    full_logs_path = execute_full_context(workflows_path)
    
    print("\n=== Phase 3: Compressed Context Execution ===")
    compressed_logs_path = execute_compressed_context(workflows_path)
    
    print("\n=== Phase 4: Analysis ===")
    # Run tradeoff model analysis
    analysis_main()
    
    # Run Bonferroni correction
    bonferroni_main()
    
    # Run threshold detection
    threshold_main()
    
    print("\n=== Phase 5: Finalizing State Registry ===")
    finalize_state_main()
    
    print("\n=== Pipeline Complete ===")

def main():
    parser = argparse.ArgumentParser(description="llmXive Pipeline Orchestrator")
    parser.add_argument('--generate', action='store_true', help='Generate synthetic workflows')
    parser.add_argument('--compress', action='store_true', help='Run compressed context execution')
    parser.add_argument('--analyze', action='store_true', help='Run analysis on generated data')
    parser.add_argument('--count', type=int, default=500, help='Number of workflows to generate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for generation')
    
    args = parser.parse_args()
    
    if args.generate and args.compress and args.analyze:
        # Run full pipeline
        run_full_pipeline(generate_count=args.count, seed=args.seed)
    elif args.generate:
        ensure_directories()
        generate_workflows(count=args.count, seed=args.seed)
    elif args.compress:
        # Assuming workflows already exist
        workflows_path = "data/raw/workflows.json"
        if not os.path.exists(workflows_path):
            print("Error: Workflows not found. Run with --generate first.")
            sys.exit(1)
        execute_full_context(workflows_path)
        execute_compressed_context(workflows_path)
    elif args.analyze:
        # Run analysis on existing data
        analysis_main()
        bonferroni_main()
        threshold_main()
        finalize_state_main()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()