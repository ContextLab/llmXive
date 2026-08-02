"""
Main entry point for the llmXive pipeline.
Orchestrates the transformation, evaluation, and analysis stages.
"""

import argparse
import sys
import os
from datetime import datetime

# Import pipeline stages
from transform.generator import generate_all_variants
from transform.metrics import run_transformation_metrics
from evaluate.dataset_balancer import run_dataset_balancing
from evaluate.runner import run_evaluation_pipeline
from analyze.report_gen import run_analysis_pipeline


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="llmXive Pipeline: Evaluate Impact of Code Style on LLM Performance"
    )
    
    subparsers = parser.add_subparsers(dest="stage", help="Pipeline stage to execute")

    # Transform Stage
    transform_parser = subparsers.add_parser("transform", help="Generate style variants")
    transform_parser.add_argument(
        "--input-dir", 
        type=str, 
        default="data/raw",
        help="Directory containing base Python functions"
    )
    transform_parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/derived",
        help="Directory to save generated variants"
    )
    transform_parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for reproducibility"
    )

    # Evaluate Stage
    eval_parser = subparsers.add_parser("evaluate", help="Run LLM tasks and collect metrics")
    eval_parser.add_argument(
        "--variants-file", 
        type=str, 
        default="data/derived/variants.json",
        help="Path to the generated variants file"
    )
    eval_parser.add_argument(
        "--output-file", 
        type=str, 
        default="results/metrics_raw.csv",
        help="Path to save raw metrics"
    )
    eval_parser.add_argument(
        "--model-name", 
        type=str, 
        default="Salesforce/codegen-2B-mono",
        help="HuggingFace model name for inference"
    )
    eval_parser.add_argument(
        "--tasks", 
        type=str, 
        nargs="+", 
        default=["completion", "bug_detection", "summarization"],
        help="Tasks to execute"
    )

    # Analyze Stage
    analyze_parser = subparsers.add_parser("analyze", help="Statistical analysis and reporting")
    analyze_parser.add_argument(
        "--metrics-file", 
        type=str, 
        default="results/metrics_raw.csv",
        help="Path to raw metrics CSV"
    )
    analyze_parser.add_argument(
        "--output-report", 
        type=str, 
        default="results/analysis_report.pdf",
        help="Path to save PDF report"
    )
    analyze_parser.add_argument(
        "--output-summary", 
        type=str, 
        default="results/statistical_summary.csv",
        help="Path to save statistical summary CSV"
    )

    return parser.parse_args()


def run_transform_stage(args):
    """Execute the transformation stage."""
    print(f"[{datetime.now().isoformat()}] Starting Transform Stage...")
    print(f"  Input: {args.input_dir}")
    print(f"  Output: {args.output_dir}")
    print(f"  Seed: {args.seed}")

    # Generate all 8-way factorial variants
    generate_all_variants(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        seed=args.seed
    )

    # Calculate and save transformation metrics
    run_transformation_metrics(
        variants_dir=args.output_dir,
        output_file="results/transformation_success_rate.json"
    )

    print(f"[{datetime.now().isoformat()}] Transform Stage completed successfully.")
    return True


def run_evaluate_stage(args):
    """Execute the evaluation stage."""
    print(f"[{datetime.now().isoformat()}] Starting Evaluate Stage...")
    print(f"  Variants: {args.variants_file}")
    print(f"  Output: {args.output_file}")
    print(f"  Model: {args.model_name}")
    print(f"  Tasks: {', '.join(args.tasks)}")

    # Step 1: Balance the dataset (clean vs mutated)
    # This prepares the data for evaluation by ensuring 50/50 split
    run_dataset_balancing(
        clean_file="data/derived/variants.json",
        mutated_file="data/derived/mutated.json",
        output_file="data/derived/balanced_dataset.csv"
    )

    # Step 2: Run the actual LLM evaluation
    run_evaluation_pipeline(
        dataset_file="data/derived/balanced_dataset.csv",
        output_file=args.output_file,
        model_name=args.model_name,
        tasks=args.tasks
    )

    print(f"[{datetime.now().isoformat()}] Evaluate Stage completed successfully.")
    return True


def run_analyze_stage(args):
    """Execute the analysis stage."""
    print(f"[{datetime.now().isoformat()}] Starting Analyze Stage...")
    print(f"  Metrics: {args.metrics_file}")
    print(f"  Report: {args.output_report}")
    print(f"  Summary: {args.output_summary}")

    run_analysis_pipeline(
        metrics_file=args.metrics_file,
        report_path=args.output_report,
        summary_path=args.output_summary
    )

    print(f"[{datetime.now().isoformat()}] Analyze Stage completed successfully.")
    return True


def main():
    """Main entry point."""
    args = parse_args()

    if not args.stage:
        print("Error: No stage specified. Use --help for usage.")
        sys.exit(1)

    success = False

    try:
        if args.stage == "transform":
            success = run_transform_stage(args)
        elif args.stage == "evaluate":
            success = run_evaluate_stage(args)
        elif args.stage == "analyze":
            success = run_analyze_stage(args)
        else:
            print(f"Error: Unknown stage '{args.stage}'")
            sys.exit(1)

        if success:
            print(f"Pipeline stage '{args.stage}' finished successfully.")
            sys.exit(0)
        else:
            print(f"Pipeline stage '{args.stage}' failed.")
            sys.exit(1)

    except Exception as e:
        print(f"Error during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()