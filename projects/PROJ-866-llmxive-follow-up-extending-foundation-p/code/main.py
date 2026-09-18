import argparse
import json
import os
import sys
import random
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure deterministic seeding at the very start of the main orchestrator
# This satisfies T048: Determinism Check
def _ensure_determinism(seed: int = 42) -> None:
    """Explicitly seed all random number generators for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def ensure_directories() -> None:
    """Create required data directories."""
    dirs = [
        "data", "data/raw", "data/processed", "data/results",
        "state", "state/projects", "contracts"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def generate_workflows(count: int, output_dir: str, seed: int) -> None:
    """Generate synthetic workflows."""
    _ensure_determinism(seed)
    from generators.synthetic_workflow import SyntheticWorkflowGenerator
    
    generator = SyntheticWorkflowGenerator(seed=seed)
    workflows = generator.generate_workflows(count)
    generator.save_workflows(workflows, output_dir)
    print(f"Generated {count} workflows to {output_dir}")

def validate_with_oracle(workflow_path: str, output_path: str) -> None:
    """Run Oracle validation on a single workflow."""
    from engines.oracle_policy import OraclePolicyEngine
    
    engine = OraclePolicyEngine()
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    result = engine.validate(workflow)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

def execute_full_context(workflow_path: str, output_path: str) -> None:
    """Execute workflow with full context."""
    from engines.full_context import FullContextEngine
    
    engine = FullContextEngine()
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    log = engine.execute(workflow)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(log, f, indent=2)

def execute_compressed_context(
    workflow_path: str, depth: int, method: str, output_path: str
) -> None:
    """Execute workflow with compressed context."""
    from engines.compressed_context import CompressedContextEngine
    
    engine = CompressedContextEngine(method=method)
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    log = engine.execute(workflow, depth=depth)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(log, f, indent=2)

def run_full_pipeline(
    generate_count: int,
    generate_seed: int,
    compress_depths: List[int],
    compress_method: str,
    analyze: bool
) -> None:
    """Run the full pipeline: Generate -> Full Exec -> Compressed Exec -> Analyze."""
    import glob
    
    # 1. Generate
    ensure_directories()
    raw_dir = "data/raw"
    generate_workflows(generate_count, raw_dir, generate_seed)
    
    # 2. Full Context Execution
    processed_dir = "data/processed"
    workflow_files = sorted(glob.glob(os.path.join(raw_dir, "wf_*.json")))
    
    print(f"Executing {len(workflow_files)} workflows with full context...")
    for wf_path in workflow_files:
        wf_id = Path(wf_path).stem
        out_path = os.path.join(processed_dir, f"full_{wf_id}.json")
        execute_full_context(wf_path, out_path)
    
    # 3. Compressed Context Execution
    print(f"Executing compressed context for depths {compress_depths}...")
    for depth in compress_depths:
        for wf_path in workflow_files:
            wf_id = Path(wf_path).stem
            out_path = os.path.join(processed_dir, f"compressed_{wf_id}_depth{depth}.json")
            execute_compressed_context(wf_path, depth, compress_method, out_path)
    
    # 4. Analysis
    if analyze:
        print("Running analysis...")
        from analysis.tradeoff_model import run_analysis
        from analysis.bonferroni_correction import main as run_bonferroni
        from analysis.threshold_detection import main as run_threshold
        from analysis.generate_regression_data import main as run_regression_data
        
        # Collect logs
        full_logs = [f for f in glob.glob(os.path.join(processed_dir, "full_*.json"))]
        compressed_logs = [f for f in glob.glob(os.path.join(processed_dir, "compressed_*.json"))]
        
        if not full_logs or not compressed_logs:
            print("Error: No logs found for analysis.")
            return

        # Run Tradeoff Model
        run_analysis()
        
        # Run Bonferroni Correction
        run_bonferroni()
        
        # Run Threshold Detection
        run_threshold()
        
        # Generate Regression Data CSV
        run_regression_data()
        
        print("Analysis complete. Results saved to data/results/")

def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="llmXive Orchestrator")
    parser.add_argument("--generate", type=int, default=0, help="Number of workflows to generate")
    parser.add_argument("--compress", action="store_true", help="Run compression execution")
    parser.add_argument("--analyze", action="store_true", help="Run analysis phase")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for generation")
    parser.add_argument("--depths", type=int, nargs="+", default=[1, 2, 3, 4, 5], help="Compression depths")
    parser.add_argument("--method", type=str, default="bfs", choices=["bfs", "dfs"], help="Compression method")
    
    args = parser.parse_args()
    
    if args.generate > 0:
        run_full_pipeline(
            generate_count=args.generate,
            generate_seed=args.seed,
            compress_depths=args.depths if args.compress else [],
            compress_method=args.method,
            analyze=args.analyze
        )
    elif args.compress or args.analyze:
        # Resume analysis without regeneration
        run_full_pipeline(
            generate_count=0,
            generate_seed=args.seed,
            compress_depths=args.depths if args.compress else [],
            compress_method=args.method,
            analyze=args.analyze
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
