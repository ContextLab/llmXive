import ast
import json
import os
import hashlib
import sys
from typing import List, Dict, Any

# Import from validation module as per API surface
from validation import (
    calculate_loc,
    calculate_cyclomatic_complexity,
    analyze_file_metrics,
    scan_repository_for_metrics,
    evaluate_repository_rubric,
    run_rubric_on_candidates
)
from data_collection import calculate_checksum, update_checksums

def ensure_dirs():
    """Ensure required output directories exist."""
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/checksums", exist_ok=True)

def clone_or_fetch_repo(repo_url: str, target_dir: str):
    """Clone or fetch a repository to target directory."""
    import subprocess
    if os.path.exists(target_dir):
        subprocess.run(["git", "-C", target_dir, "fetch", "origin"], check=True)
    else:
        subprocess.run(["git", "clone", repo_url, target_dir], check=True)

def process_repo(repo_path: str, candidate_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single repository: calculate LOC, CC, run rubric, and determine exclusion.
    Returns a metrics dictionary.
    """
    # Calculate file-level metrics
    file_metrics = analyze_file_metrics(repo_path)
    
    # Aggregate repository-level metrics
    total_loc = sum(f['loc'] for f in file_metrics)
    total_cc = sum(f['cyclomatic_complexity'] for f in file_metrics)
    avg_cc = total_cc / len(file_metrics) if file_metrics else 0

    # Run documentation rubric
    rubric_result = evaluate_repository_rubric(repo_path)
    
    # Determine exclusion
    is_excluded = not rubric_result.get('passed', False)
    
    return {
        "repo_url": candidate_info.get('url', ''),
        "repo_name": os.path.basename(repo_path),
        "loc": total_loc,
        "cyclomatic_complexity": total_cc,
        "average_cyclomatic_complexity": round(avg_cc, 2),
        "file_count": len(file_metrics),
        "rubric_score": rubric_result.get('score', 0),
        "rubric_details": rubric_result.get('details', {}),
        "passed_rubric": rubric_result.get('passed', False),
        "excluded": is_excluded
    }

def generate_checksum(file_path: str) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for T021b.
    1. Reads candidate repos from a config or defaults to a list.
    2. Processes each repo (metrics + rubric).
    3. Writes repo_selection_rubric.json and repo_metrics.json.
    4. Generates checksum for repo_selection_rubric.json and appends to data/checksums.txt.
    """
    ensure_dirs()

    # Default candidate repos if no external config is provided
    # In a real scenario, this would be loaded from a spec file or database
    candidates = [
        {"url": "https://github.com/psf/requests", "name": "requests"},
        {"url": "https://github.com/pallets/flask", "name": "flask"},
        {"url": "https://github.com/pytest-dev/pytest", "name": "pytest"}
    ]

    all_metrics = []
    rubric_results = []

    for candidate in candidates:
        repo_name = candidate['name']
        target_dir = os.path.join("data/raw", "temp_repos", repo_name)
        
        try:
            clone_or_fetch_repo(candidate['url'], target_dir)
            metrics = process_repo(target_dir, candidate)
            all_metrics.append(metrics)
            
            if not metrics['passed_rubric']:
                print(f"Excluding repo: {repo_name} (Rubric failed)")
            
            rubric_results.append({
                "repo": repo_name,
                "url": candidate['url'],
                "rubric_score": metrics['rubric_score'],
                "passed": metrics['passed_rubric'],
                "excluded": metrics['excluded'],
                "details": metrics['rubric_details']
            })
        except Exception as e:
            print(f"Error processing {repo_name}: {e}")
            # Record failed repo as excluded
            rubric_results.append({
                "repo": repo_name,
                "url": candidate['url'],
                "rubric_score": 0,
                "passed": False,
                "excluded": True,
                "details": {"error": str(e)}
            })
            all_metrics.append({
                "repo_url": candidate['url'],
                "repo_name": repo_name,
                "loc": 0,
                "cyclomatic_complexity": 0,
                "average_cyclomatic_complexity": 0,
                "file_count": 0,
                "rubric_score": 0,
                "rubric_details": {"error": str(e)},
                "passed_rubric": False,
                "excluded": True
            })

    # Write outputs
    metrics_path = "data/raw/repo_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    
    rubric_path = "data/raw/repo_selection_rubric.json"
    with open(rubric_path, "w") as f:
        json.dump(rubric_results, f, indent=2)

    # Generate checksum for rubric file
    checksum = generate_checksum(rubric_path)
    
    # Append to checksums.txt
    checksum_file = "data/checksums.txt"
    with open(checksum_file, "a") as f:
        f.write(f"{rubric_path}:{checksum}\n")
    
    print(f"Metrics written to {metrics_path}")
    print(f"Rubric results written to {rubric_path}")
    print(f"Checksum recorded: {checksum}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
