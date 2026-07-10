"""
T021b: Execute rubric on candidate repos, calculate LOC/CC metrics,
generate JSON reports, implement exclusion logic, and record checksums.

This script:
1. Loads candidate repository definitions (from a config or hardcoded list for this task).
2. Executes the rubric defined in T021a via validation.py.
3. Calculates LOC and Cyclomatic Complexity using validation.py utilities.
4. Writes data/raw/repo_selection_rubric.json and data/raw/repo_metrics.json.
5. Filters out failing repos based on the rubric.
6. Generates a checksum for repo_selection_rubric.json and appends to data/checksums.txt.
"""

import ast
import json
import os
import hashlib
import sys
from typing import List, Dict, Any

# Ensure we can import from the project's code directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.validation import (
    check_documentation_criteria,
    evaluate_repository_rubric,
    calculate_loc,
    calculate_cyclomatic_complexity,
    scan_repository_for_metrics
)

# Configuration for candidate repositories
# In a real scenario, this might come from a config file or CLI argument.
# For this task, we define a small set of real, public Python repositories.
CANDIDATE_REPOS = [
    {
        "name": "requests",
        "url": "https://github.com/psf/requests.git",
        "local_path": "data/raw/repos/requests"
    },
    {
        "name": "python-dateutil",
        "url": "https://github.com/dateutil/dateutil.git",
        "local_path": "data/raw/repos/python-dateutil"
    },
    {
        "name": "fake-repo-no-docs",
        "url": "https://github.com/example/nonexistent-repo.git", # Intentionally failing for exclusion logic test
        "local_path": "data/raw/repos/fake-repo-no-docs"
    }
]

def ensure_dirs():
    """Ensure output directories exist."""
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/raw/repos", exist_ok=True)
    os.makedirs("data/checksums", exist_ok=True)

def clone_or_fetch_repo(repo_config: Dict[str, Any]) -> bool:
    """
    Clone a repository if it doesn't exist, otherwise assume it's present.
    Returns True if successful, False otherwise.
    """
    import subprocess
    import shutil

    path = repo_config["local_path"]
    url = repo_config["url"]

    if os.path.exists(path):
        # Simple check if it's a git repo with content
        if os.path.exists(os.path.join(path, ".git")):
            return True
        else:
            # Clean up stale directory
            shutil.rmtree(path)
    
    try:
        # Clone the repo
        subprocess.run(
            ["git", "clone", "--depth", "1", url, path],
            check=True,
            capture_output=True,
            timeout=60
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False

def process_repo(repo_config: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single repository: clone, evaluate, metrics."""
    result = {
        "name": repo_config["name"],
        "url": repo_config["url"],
        "success": False,
        "rubric_score": None,
        "metrics": None,
        "excluded": False,
        "error": None
    }

    if not clone_or_fetch_repo(repo_config):
        result["error"] = "Failed to clone repository"
        result["excluded"] = True
        return result

    repo_path = repo_config["local_path"]

    # 1. Execute Rubric (T021a logic)
    try:
        # We need to simulate the check_documentation_criteria logic
        # Since T021a is implemented, we assume check_documentation_criteria exists
        # and returns a dict of criteria checks.
        criteria_results = check_documentation_criteria(repo_path)
        rubric_result = evaluate_repository_rubric(criteria_results)
        
        result["rubric_score"] = rubric_result
        
        # Exclusion Logic: If score < threshold (e.g., 0.5), exclude
        if rubric_result.get("final_score", 0) < 0.5:
            result["excluded"] = True
            result["error"] = "Failed rubric threshold"
            # Still collect metrics for record, but mark excluded
    except Exception as e:
        result["error"] = f"Rubric evaluation failed: {str(e)}"
        result["excluded"] = True
        # Continue to metrics if possible, but mark as failed rubric

    # 2. Calculate Metrics (LOC, CC)
    try:
        # scan_repository_for_metrics returns a dict of file metrics
        file_metrics = scan_repository_for_metrics(repo_path)
        
        total_loc = 0
        total_cc = 0
        file_count = 0

        for file_path, metrics in file_metrics.items():
            if metrics:
                total_loc += metrics.get("loc", 0)
                total_cc += metrics.get("cyclomatic_complexity", 0)
                file_count += 1

        result["metrics"] = {
            "total_loc": total_loc,
            "total_cyclomatic_complexity": total_cc,
            "file_count": file_count,
            "average_loc_per_file": total_loc / file_count if file_count > 0 else 0,
            "average_cc_per_file": total_cc / file_count if file_count > 0 else 0
        }
        result["success"] = True
    except Exception as e:
        result["error"] = f"Metric calculation failed: {str(e)}"
        if result["rubric_score"] is None:
            result["excluded"] = True

    return result

def generate_checksum(file_path: str) -> str:
    """Generate SHA-256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    ensure_dirs()

    print("Starting T021b: Repository Rubric Execution and Metrics Collection")

    all_results = []
    for repo in CANDIDATE_REPOS:
        print(f"Processing {repo['name']}...")
        result = process_repo(repo)
        all_results.append(result)
        print(f"  - Excluded: {result['excluded']}, Error: {result['error']}")

    # 3. Generate repo_selection_rubric.json
    rubric_output_path = "data/raw/repo_selection_rubric.json"
    with open(rubric_output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"Written: {rubric_output_path}")

    # 4. Generate repo_metrics.json (Filtered: only successful, non-excluded repos)
    metrics_output_path = "data/raw/repo_metrics.json"
    valid_metrics = [r for r in all_results if not r.get("excluded", True) and r.get("success", False)]
    
    metrics_data = {
        "timestamp": str(__import__('datetime').datetime.now()),
        "repos": valid_metrics
    }
    
    with open(metrics_output_path, "w") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Written: {metrics_output_path} (containing {len(valid_metrics)} valid repos)")

    # 5. Generate Checksum for repo_selection_rubric.json
    checksum = generate_checksum(rubric_output_path)
    checksum_file_path = "data/checksums.txt"
    
    # Append to existing checksums file
    with open(checksum_file_path, "a") as f:
        f.write(f"{checksum}  repo_selection_rubric.json\n")
    
    print(f"Checksum recorded in {checksum_file_path}: {checksum}")

    # Verification
    if os.path.exists(rubric_output_path) and os.path.exists(metrics_output_path) and os.path.exists(checksum_file_path):
        print("Verification: All required files exist.")
        return 0
    else:
        print("Verification: Missing required files.")
        return 1

if __name__ == "__main__":
    sys.exit(main())