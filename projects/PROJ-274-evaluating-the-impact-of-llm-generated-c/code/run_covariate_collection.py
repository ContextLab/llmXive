"""
Script to generate repo_covariates.json from repo_metrics.json and repo_matching_report.json.
This prepares the covariate data for ANCOVA analysis.
"""
import json
import os
import sys
from validation import generate_covariates_json

def main():
    """
    Main entry point to generate covariates.
    Reads:
      - data/raw/repo_metrics.json (from T021c)
      - data/raw/repo_matching_report.json (from T021d)
    Writes:
      - data/raw/repo_covariates.json
    """
    # Define paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metrics_path = os.path.join(project_root, "data", "raw", "repo_metrics.json")
    matching_path = os.path.join(project_root, "data", "raw", "repo_matching_report.json")
    output_path = os.path.join(project_root, "data", "raw", "repo_covariates.json")

    # Check input files exist
    if not os.path.exists(metrics_path):
        print(f"Error: Input file not found: {metrics_path}", file=sys.stderr)
        print("Please ensure T021c has been executed successfully.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(matching_path):
        print(f"Error: Input file not found: {matching_path}", file=sys.stderr)
        print("Please ensure T021d has been executed successfully.", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Generate covariates
    try:
        generate_covariates_json(metrics_path, matching_path, output_path)
        print(f"Successfully generated covariates: {output_path}")
    except Exception as e:
        print(f"Error generating covariates: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
