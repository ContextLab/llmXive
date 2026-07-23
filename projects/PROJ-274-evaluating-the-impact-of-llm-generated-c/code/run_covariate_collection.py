import json
import os
import sys
from validation import generate_covariates_json

def main():
    """
    Main entry point for collecting covariates.
    Reads candidate repositories from a config or environment, 
    processes them, and writes data/raw/repo_covariates.json.
    """
    # Default paths based on project structure
    output_file = "data/raw/repo_covariates.json"
    
    # If no arguments provided, look for a default candidate list or env var
    # For now, we expect the caller to provide the list or we define a default
    # In a real pipeline, this would be driven by the output of T021b (repo_selection_rubric.json)
    
    candidate_repos = []
    
    # Attempt to load candidates from the rubric output if it exists
    rubric_path = "data/raw/repo_selection_rubric.json"
    if os.path.exists(rubric_path):
        try:
            with open(rubric_path, 'r') as f:
                rubric_data = json.load(f)
                # Assuming rubric_data is a list of dicts with 'repo_path'
                for item in rubric_data:
                    if isinstance(item, dict) and 'repo_path' in item:
                        candidate_repos.append(item['repo_path'])
        except Exception as e:
            print(f"Warning: Could not load {rubric_path}: {e}. Using empty list.", file=sys.stderr)
    else:
        print(f"Warning: {rubric_path} not found. No candidates to process.", file=sys.stderr)

    if not candidate_repos:
        print("No candidate repositories found to process.", file=sys.stderr)
        # Create an empty output file to satisfy the task requirement of producing the file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump([], f)
        return

    print(f"Processing {len(candidate_repos)} repositories for covariates...")
    checksum = generate_covariates_json(candidate_repos, output_file)
    
    print(f"Covariates written to {output_file}")
    print(f"Checksum: {checksum}")

    # Append checksum to checksums.txt if it exists
    checksum_file = "data/checksums.txt"
    os.makedirs(os.path.dirname(checksum_file), exist_ok=True)
    with open(checksum_file, 'a') as f:
        f.write(f"{output_file}: {checksum}\n")
    
    print(f"Checksum appended to {checksum_file}")

if __name__ == "__main__":
    main()