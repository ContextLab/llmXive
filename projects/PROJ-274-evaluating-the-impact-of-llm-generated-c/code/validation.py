"""
Validation module for repository selection and rubric scoring.
Contains functions for loading/saving JSON, calculating metrics,
and evaluating documentation quality.
"""
import ast
import json
import os
import glob
import hashlib
import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# --- Utility Functions ---

def load_json_file(filepath: str) -> Any:
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Any, filepath: str) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def calculate_file_checksum(filepath: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def update_checksums(data: List[Dict], filepath: str) -> List[Dict]:
    """Add checksums to data entries if they reference files."""
    for item in data:
        if 'file_path' in item and os.path.exists(item['file_path']):
            item['checksum'] = calculate_file_checksum(item['file_path'])
    return data

# --- Repository Loading ---

def load_candidate_repos(filepath: str) -> List[Dict]:
    """
    Load candidate repositories from a JSON file.
    Expected format: [{"name": "repo_name", "path": "/path/to/repo"}, ...]
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Candidate repos file not found: {filepath}")
    return load_json_file(filepath)

# --- Metrics Collection (T021a, T021b) ---

def calculate_cyclomatic_complexity(repo_path: str) -> float:
    """
    Calculate average cyclomatic complexity for a repository using radon.
    Runs: radon cc -a -s <repo_path>
    """
    try:
        # Note: This assumes radon is installed and in PATH
        result = subprocess.run(
            ['radon', 'cc', '-a', '-s', repo_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode != 0:
            logger.warning(f"Radon failed for {repo_path}: {result.stderr}")
            return 0.0
        
        # Parse output: Expected format like "A 2.00 (avg)" or similar
        # We look for the average value
        lines = result.stdout.split('\n')
        for line in lines:
            if 'avg' in line.lower():
                # Extract number
                match = re.search(r'([\d.]+)', line)
                if match:
                    return float(match.group(1))
        return 0.0
    except FileNotFoundError:
        logger.error("radon command not found. Please install it.")
        return 0.0
    except Exception as e:
        logger.error(f"Error calculating CC for {repo_path}: {e}")
        return 0.0

def calculate_loc(repo_path: str) -> int:
    """
    Calculate Lines of Code for a repository using cloc.
    Runs: cloc --json <repo_path>
    """
    try:
        result = subprocess.run(
            ['cloc', '--json', repo_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode != 0:
            logger.warning(f"cloc failed for {repo_path}: {result.stderr}")
            return 0
        
        data = json.loads(result.stdout)
        # cloc output structure: {"sum": {"nCode": 12345}, ...}
        if 'sum' in data and 'nCode' in data['sum']:
            return int(data['sum']['nCode'])
        return 0
    except FileNotFoundError:
        logger.error("cloc command not found. Please install it.")
        return 0
    except Exception as e:
        logger.error(f"Error calculating LOC for {repo_path}: {e}")
        return 0

# --- Documentation Rubric (T021c) ---

def check_documentation_criteria(repo_name: str, repo_path: str) -> Dict[str, bool]:
    """
    Check for the presence of specific documentation sections in a repository.
    Criteria: Setup, API, Architecture.
    
    Looks for README.md, docs/ directory, or specific files.
    """
    criteria = {
        "setup": False,
        "api": False,
        "architecture": False
    }
    
    # List of potential documentation files to search
    potential_files = []
    readme_paths = [
        os.path.join(repo_path, 'README.md'),
        os.path.join(repo_path, 'readme.md'),
        os.path.join(repo_path, 'README.rst'),
        os.path.join(repo_path, 'README.txt'),
        os.path.join(repo_path, 'docs', 'README.md'),
        os.path.join(repo_path, 'docs', 'index.md')
    ]
    
    for p in readme_paths:
        if os.path.isfile(p):
            potential_files.append(p)
    
    # Also check docs folder if it exists
    docs_dir = os.path.join(repo_path, 'docs')
    if os.path.isdir(docs_dir):
        for f in os.listdir(docs_dir):
            if f.endswith(('.md', '.rst', '.txt')):
                potential_files.append(os.path.join(docs_dir, f))
    
    if not potential_files:
        logger.debug(f"No documentation files found for {repo_name}")
        return criteria

    # Search content for keywords
    keywords = {
        "setup": ["setup", "install", "installation", "getting started", "prereq"],
        "api": ["api", "application programming interface", "endpoint", "method", "function reference"],
        "architecture": ["architecture", "design", "structure", "overview", "components"]
    }

    for file_path in potential_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().lower()
            
            for criterion, words in keywords.items():
                if not criteria[criterion]:
                    for word in words:
                        if word in content:
                            criteria[criterion] = True
                            break
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")

    return criteria

def calculate_doc_quality_score(criteria: Dict[str, bool]) -> int:
    """
    Calculate the total score (0-3) based on binary indicators.
    """
    return sum(1 for v in criteria.values() if v)

def evaluate_repository_rubric(repo_name: str, repo_path: str) -> Dict[str, Any]:
    """
    Evaluate a single repository against the documentation rubric.
    Returns a dictionary with total score and individual criteria status.
    """
    criteria = check_documentation_criteria(repo_name, repo_path)
    total_score = calculate_doc_quality_score(criteria)
    
    return {
        "total_score": total_score,
        "criteria": criteria
    }

def run_rubric_on_candidates(candidates: List[Dict]) -> List[Dict]:
    """
    Run the rubric evaluation on a list of candidate repositories.
    """
    results = []
    for repo in candidates:
        name = repo.get("name", "unknown")
        path = repo.get("path") or repo.get("url")
        if not path:
            continue
        
        score_details = evaluate_repository_rubric(name, path)
        results.append({
            "repo_name": name,
            "repo_path": path,
            "rubric_score": score_details["total_score"],
            "details": score_details["criteria"]
        })
    return results

# --- Metric Aggregation & Filtering (T021d, T021f, T021g) ---

def calculate_baseline_stats(metrics_list: List[float]) -> Dict[str, float]:
    """Calculate median and std dev for a list of metrics."""
    if not metrics_list:
        return {"median": 0, "std": 0}
    sorted_metrics = sorted(metrics_list)
    n = len(sorted_metrics)
    median = sorted_metrics[n // 2] if n % 2 == 1 else (sorted_metrics[n // 2 - 1] + sorted_metrics[n // 2]) / 2
    
    mean = sum(sorted_metrics) / n
    variance = sum((x - mean) ** 2 for x in sorted_metrics) / n if n > 0 else 0
    std = variance ** 0.5
    
    return {"median": median, "std": std}

def evaluate_matching_quality(repo_metrics: Dict, baseline: Dict, tolerance: float = 0.15) -> bool:
    """
    Check if repo metrics are within ±15% of the baseline median.
    """
    median = baseline.get("median", 0)
    if median == 0:
        return False
    lower = median * (1 - tolerance)
    upper = median * (1 + tolerance)
    return lower <= repo_metrics <= upper

def collect_metrics_for_covariates(repos: List[Dict], loc_data: Dict, cc_data: Dict) -> List[Dict]:
    """
    Aggregate LOC, CC, and Doc Quality into a single dataset.
    """
    covariates = []
    for repo in repos:
        name = repo.get("name")
        loc = loc_data.get(name, {}).get("loc", 0)
        cc = cc_data.get(name, {}).get("cc", 0)
        doc_score = repo.get("rubric_score", 0)
        
        covariates.append({
            "repo_name": name,
            "loc": loc,
            "cc": cc,
            "doc_quality": doc_score
        })
    return covariates

def generate_covariates_json(repos: List[Dict], loc_file: str, cc_file: str, output_file: str):
    """
    Generate the final covariates JSON file.
    """
    loc_data = load_json_file(loc_file) if os.path.exists(loc_file) else {}
    cc_data = load_json_file(cc_file) if os.path.exists(cc_file) else {}
    
    # Re-load repos if they are just names, or assume passed list has scores
    # Assuming repos list comes from previous step with scores
    final_data = collect_metrics_for_covariates(repos, loc_data, cc_data)
    
    save_json_file(final_data, output_file)

# --- Main Entry Point for Module Testing ---
def main():
    """
    Main function for direct execution if needed for debugging.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Validation module loaded.")

if __name__ == "__main__":
    main()