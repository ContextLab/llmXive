import json
import os
import sys
from validation import generate_covariates_json

def main():
    """
    Main entry point for running covariate collection.
    Reads candidate repos from data/raw/repo_selection_rubric.json
    and outputs covariates to data/raw/repo_covariates.json.
    """
    # Load candidate repos from rubric output
    rubric_path = "data/raw/repo_selection_rubric.json"
    
    if not os.path.exists(rubric_path):
        print(f"Error: {rubric_path} not found. Run T021b first.")
        sys.exit(1)
    
    with open(rubric_path, 'r') as f:
        rubric_data = json.load(f)
    
    # Extract passed repos
    candidate_repos = [
        item["repo_path"] for item in rubric_data.get("results", [])
        if item.get("passed", False)
    ]
    
    if not candidate_repos:
        print("No passed repositories found. Cannot generate covariates.")
        sys.exit(1)
    
    print(f"Generating covariates for {len(candidate_repos)} repositories...")
    
    output_path = "data/raw/repo_covariates.json"
    generate_covariates_json(candidate_repos, output_path)
    
    print(f"Covariates generated successfully: {output_path}")

if __name__ == "__main__":
    main()