"""
Validation and Rubric Logic for Repository Selection and Documentation Quality.

Implements:
- Repository selection rubric (T021a)
- Metric collection (T021c)
- Documentation Quality Rubric Scoring (T021f)
- Covariate generation (T021e, T021g)
"""
import ast
import json
import os
import glob
import hashlib
import re
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Logging setup is handled in runners to avoid circular import issues with 'logging' module name conflicts
# We assume logging is configured by the caller.

def calculate_loc(repo_path: str) -> int:
    """Calculate Lines of Code using cloc."""
    try:
        result = subprocess.run(
            ['cloc', '--json', repo_path],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        # Sum 'code' lines across all languages
        total_code = sum(
            repo_data.get('code', 0) 
            for repo_data in data.values() 
            if isinstance(repo_data, dict) and 'code' in repo_data
        )
        return total_code
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        raise RuntimeError(f"Failed to calculate LOC for {repo_path}: {e}")

def calculate_cyclomatic_complexity(repo_path: str) -> float:
    """Calculate average Cyclomatic Complexity using radon."""
    try:
        result = subprocess.run(
            ['radon', 'cc', '-a', '-s', '-j', repo_path],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        if not data:
            return 0.0
        
        total_complexity = 0
        count = 0
        for file_data in data:
            for func in file_data.get('functions', []):
                total_complexity += func.get('complexity', 0)
                count += 1
            # Also consider classes? radon cc usually handles methods inside classes too.
            # If 'classes' are separate in radon output, we'd add them. 
            # Standard radon cc -a aggregates.
        
        return total_complexity / count if count > 0 else 0.0
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        raise RuntimeError(f"Failed to calculate CC for {repo_path}: {e}")

def collect_metrics_for_covariates(repo_path: str) -> Dict[str, Any]:
    """Collect LOC and CC metrics for a repository."""
    return {
        "loc": calculate_loc(repo_path),
        "cc": calculate_cyclomatic_complexity(repo_path)
    }

def check_documentation_criteria(doc_path: str) -> bool:
    """Check if a file exists and is non-empty."""
    return os.path.isfile(doc_path) and os.path.getsize(doc_path) > 0

def calculate_doc_quality_score(repo_path: str) -> Dict[str, Any]:
    """
    T021f: Calculate Documentation Quality Rubric Score.
    
    Checks for the presence of:
    1. Setup Instructions (README, INSTALL, etc.)
    2. API Reference (API.md, docs/api, etc.)
    3. Architecture Documentation (ARCHITECTURE.md, docs/architecture, etc.)
    
    Returns a dict with binary indicators and total score (max 3).
    """
    repo_path = Path(repo_path)
    if not repo_path.is_dir():
        return {
            "total_score": 0,
            "has_setup": False,
            "has_api": False,
            "has_architecture": False
        }

    # Patterns to look for (case-insensitive search in filenames)
    setup_patterns = ['readme', 'install', 'getting_started', 'setup']
    api_patterns = ['api', 'reference', 'docs/api', 'docs/reference']
    arch_patterns = ['architecture', 'arch', 'design', 'structure', 'docs/architecture']

    def find_file(base_path: Path, patterns: List[str]) -> bool:
        # Check root level
        for f in base_path.iterdir():
            if f.is_file() and any(p in f.name.lower() for p in patterns):
                return True
        # Check common docs folders
        docs_dirs = [base_path / 'docs', base_path / 'documentation']
        for d in docs_dirs:
            if d.exists():
                for f in d.iterdir():
                    if f.is_file() and any(p in f.name.lower() for p in patterns):
                        return True
                # Recursive check for subfolders in docs
                for f in d.rglob('*'):
                    if f.is_file() and any(p in f.name.lower() for p in patterns):
                        return True
        return False

    has_setup = find_file(repo_path, setup_patterns)
    has_api = find_file(repo_path, api_patterns)
    has_architecture = find_file(repo_path, arch_patterns)

    total_score = sum([has_setup, has_api, has_architecture])

    return {
        "total_score": total_score,
        "has_setup": has_setup,
        "has_api": has_api,
        "has_architecture": has_architecture
    }

def evaluate_repository_rubric(repo_path: str) -> Dict[str, Any]:
    """
    Evaluate a repository against the documentation quality rubric.
    Returns the score data from calculate_doc_quality_score.
    """
    return calculate_doc_quality_score(repo_path)

def run_rubric_on_candidates(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run the documentation rubric on a list of candidate repositories.
    """
    results = []
    for repo in repos:
        path = repo.get('path') or repo.get('local_path')
        if not path:
            continue
        score_data = evaluate_repository_rubric(path)
        results.append({
            "repo_name": repo.get('name', 'Unknown'),
            **score_data
        })
    return results

def generate_covariates_json(metrics_data: List[Dict], doc_scores: List[Dict]) -> List[Dict]:
    """
    T021g: Aggregate metrics and doc scores into a single covariate dataset.
    Normalizes/centers the values for ANCOVA.
    """
    # Merge by repo name (simplified assumption: order or name matches)
    # In a real robust implementation, we'd use a unique repo ID.
    merged = {}
    
    for m in metrics_data:
        name = m.get('name')
        if name:
            merged[name] = {'loc': m.get('loc', 0), 'cc': m.get('cc', 0)}
    
    for d in doc_scores:
        name = d.get('repo_name')
        if name in merged:
            merged[name]['doc_quality'] = d.get('total_score', 0)
        else:
            # If we have a doc score but no metrics, create entry
            merged[name] = {'loc': 0, 'cc': 0, 'doc_quality': d.get('total_score', 0)}

    # Calculate means for centering
    if not merged:
        return []

    locs = [v['loc'] for v in merged.values()]
    ccs = [v['cc'] for v in merged.values()]
    docs = [v['doc_quality'] for v in merged.values()]

    mean_loc = sum(locs) / len(locs)
    mean_cc = sum(ccs) / len(ccs)
    mean_doc = sum(docs) / len(docs)

    covariates = []
    for name, data in merged.items():
        covariates.append({
            "name": name,
            "loc_centered": data['loc'] - mean_loc,
            "cc_centered": data['cc'] - mean_cc,
            "doc_quality_centered": data['doc_quality'] - mean_doc,
            # Also keep raw for reporting
            "loc_raw": data['loc'],
            "cc_raw": data['cc'],
            "doc_quality_raw": data['doc_quality']
        })

    return covariates

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(file_path: str, checksums_file: str):
    """Update the global checksums file with a new entry."""
    checksum = calculate_file_checksum(file_path)
    filename = os.path.basename(file_path)
    
    with open(checksums_file, 'a', encoding='utf-8') as f:
        f.write(f"{filename}:{checksum}\n")

def main():
    """CLI entry point for validation tasks (optional)."""
    import argparse
    parser = argparse.ArgumentParser(description="Validation and Rubric Tools")
    parser.add_argument('--mode', choices=['metrics', 'rubric', 'covariates'], required=True)
    parser.add_argument('--repo', type=str, help='Path to repository')
    parser.add_argument('--output', type=str, help='Output file path')
    args = parser.parse_args()

    if args.mode == 'metrics' and args.repo:
        metrics = collect_metrics_for_covariates(args.repo)
        print(json.dumps(metrics))
    elif args.mode == 'rubric' and args.repo:
        score = evaluate_repository_rubric(args.repo)
        print(json.dumps(score))
    elif args.mode == 'covariates':
        print("Use run_covariate_collection.py for full pipeline.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()