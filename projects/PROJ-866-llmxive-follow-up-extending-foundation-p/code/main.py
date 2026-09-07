import argparse
import json
import os
import sys
import random
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from generators.synthetic_workflow import SyntheticWorkflowGenerator
from engines.oracle_policy import OraclePolicyEngine
from engines.full_context import FullContextEngine
from engines.compressed_context import CompressedContextEngine
from engines.save_processed_logs import save_processed_logs
from analysis.tradeoff_model import run_analysis
from analysis.generate_regression_data import main as generate_regression_data_main
from analysis.threshold_detection import main as threshold_detection_main
from analysis.bonferroni_correction import main as bonferroni_main
from utils.finalize_state_registry import main as finalize_state_main


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "state",
        "state/projects",
        "contracts",
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def generate_workflows(count: int, output_dir: str, seed: int = 42) -> List[Dict[str, Any]]:
    """Generate synthetic workflows.

    Args:
        count: Number of workflows to generate.
        output_dir: Directory to save workflows.
        seed: Random seed.

    Returns:
        List of generated workflows.
    """
    generator = SyntheticWorkflowGenerator(seed=seed)
    workflows = generator.generate_workflows(count)
    generator.save_workflows(workflows, output_dir)
    return workflows


def validate_with_oracle(workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate workflows using Oracle Policy Engine.

    Args:
        workflows: List of workflows to validate.

    Returns:
        List of validation results.
    """
    oracle = OraclePolicyEngine()
    results = []

    for workflow in workflows:
        is_valid, violations = oracle.validate_workflow(workflow)
        results.append({
            "workflow_id": workflow.get("id"),
            "is_valid": is_valid,
            "violations": violations
        })

    return results


def execute_full_context(workflows: List[Dict[str, Any]], output_dir: str) -> List[Dict[str, Any]]:
    """Execute workflows with full context.

    Args:
        workflows: List of workflows to execute.
        output_dir: Directory to save logs.

    Returns:
        List of execution logs.
    """
    engine = FullContextEngine()
    logs = []

    for workflow in workflows:
        log = engine.execute(workflow)
        logs.append(log)
        # Save individual log
        filename = f"full_{workflow.get('id', 'unknown')}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(log, f, indent=2)

    return logs


def execute_compressed_context(
    workflows: List[Dict[str, Any]],
    output_dir: str,
    depths: List[int] = [1, 2, 3, 4, 5]
) -> List[Dict[str, Any]]:
    """Execute workflows with compressed context at multiple depths.

    Args:
        workflows: List of workflows to execute.
        output_dir: Directory to save logs.
        depths: List of compression depths to test.

    Returns:
        List of execution logs.
    """
    all_logs = []

    for depth in depths:
        engine = CompressedContextEngine(traversal_depth=depth)
        for workflow in workflows:
            log = engine.execute(workflow)
            all_logs.append(log)
            # Save individual log
            filename = f"compressed_{workflow.get('id', 'unknown')}_{depth}.json"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                json.dump(log, f, indent=2)

    return all_logs


def run_full_pipeline(
    num_workflows: int = 500,
    compression_depths: List[int] = [1, 2, 3, 4, 5],
    seed: int = 42
) -> None:
    """Run the full research pipeline.

    Args:
        num_workflows: Number of workflows to generate.
        compression_depths: Compression depths to test.
        seed: Random seed.
    """
    start_time = time.time()

    # Ensure directories
    ensure_directories()

    # Step 1: Generate workflows
    print("Generating workflows...")
    workflows = generate_workflows(num_workflows, "data/raw", seed)
    print(f"Generated {len(workflows)} workflows.")

    # Step 2: Full context execution
    print("Executing full context...")
    full_logs = execute_full_context(workflows, "data/processed")
    print(f"Executed {len(full_logs)} full context logs.")

    # Step 3: Compressed context execution
    print("Executing compressed context...")
    compressed_logs = execute_compressed_context(
        workflows, "data/processed", compression_depths
    )
    print(f"Executed {len(compressed_logs)} compressed context logs.")

    # Step 4: Save processed logs
    print("Saving processed logs...")
    count = save_processed_logs("data/processed", "data/processed")
    print(f"Saved {count} processed logs.")

    # Step 5: Generate regression data
    print("Generating regression data...")
    generate_regression_data_main()

    # Step 6: Bonferroni correction
    print("Applying Bonferroni correction...")
    bonferroni_main()

    # Step 7: Threshold detection
    print("Detecting threshold...")
    threshold_detection_main()

    # Step 8: Finalize state registry
    print("Finalizing state registry...")
    finalize_state_main()

    elapsed = time.time() - start_time
    print(f"Pipeline completed in {elapsed:.2f} seconds.")


def main() -> None:
    """Main entry point for the orchestrator."""
    parser = argparse.ArgumentParser(description="llmXive Research Orchestrator")
    parser.add_argument("--generate", type=int, help="Generate N workflows")
    parser.add_argument("--compress", type=int, nargs="*", default=[1, 2, 3, 4, 5],
                      help="Compression depths to test")
    parser.add_argument("--analyze", action="store_true", help="Run analysis")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--pipeline", action="store_true", help="Run full pipeline")

    args = parser.parse_args()

    if args.pipeline:
        run_full_pipeline(num_workflows=args.generate or 500, seed=args.seed)
    elif args.generate:
        ensure_directories()
        workflows = generate_workflows(args.generate, "data/raw", args.seed)
        print(f"Generated {len(workflows)} workflows.")
        if args.analyze:
            # Run analysis on generated data
            run_full_pipeline(num_workflows=args.generate, seed=args.seed)
    elif args.analyze:
        # Just run analysis on existing data
        generate_regression_data_main()
        bonferroni_main()
        threshold_detection_main()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
