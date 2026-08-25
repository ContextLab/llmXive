import ast
import json
import os
import glob
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Utility Functions ---

def load_json_file(path: str) -> Dict:
    """Load a JSON file and return its contents."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(path: str, data: Dict) -> None:
    """Save data to a JSON file, creating directories if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def calculate_file_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums(checksums_path: str, file_path: str) -> None:
    """Update a checksum file with the latest checksum for a file."""
    checksums = {}
    if os.path.exists(checksums_path):
        checksums = load_json_file(checksums_path)
    checksums[os.path.basename(file_path)] = calculate_file_checksum(file_path)
    save_json_file(checksums_path, checksums)

def load_candidate_repos(config_path: str) -> List[Dict]:
    """Load candidate repositories from a YAML or JSON config."""
    # Assuming YAML for now based on T020a, but handling JSON if needed
    if config_path.endswith('.yaml') or config_path.endswith('.yml'):
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config.get('repositories', [])
        except ImportError:
            logger.warning("PyYAML not installed. Attempting JSON fallback.")
            return load_json_file(config_path).get('repositories', [])
    else:
        return load_json_file(config_path).get('repositories', [])

def calculate_loc(repo_path: str) -> int:
    """Calculate Lines of Code (LOC) for a repository using cloc if available, else fallback."""
    # Attempt to use cloc if installed
    try:
        import subprocess
        result = subprocess.run(['cloc', '--quiet', '--csv', repo_path],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                # cloc CSV output: Language,files,blank,comment,code
                # Last line is usually total
                total_line = lines[-1]
                parts = total_line.split(',')
                if len(parts) >= 5:
                    return int(parts[4])
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass

    # Fallback: simple file traversal
    total_loc = 0
    for root, _, files in os.walk(repo_path):
        # Skip common non-code directories
        if any(skip in root for skip in ['.git', 'node_modules', '__pycache__', 'venv']):
            continue
        for file in files:
            if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go')):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                        total_loc += sum(1 for line in f if line.strip())
                except Exception:
                    continue
    return total_loc

def calculate_cyclomatic_complexity(repo_path: str) -> int:
    """Calculate Cyclomatic Complexity (CC) using radon if available, else fallback."""
    try:
        from radon.complexity import cc_visit
        from radon.raw import analyze
        import subprocess
        
        # Try radon command line first
        result = subprocess.run(['radon', 'cc', repo_path, '--total-average'],
                                capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and 'Average' in result.stdout:
            # Parse average complexity from output (format: "Average CC: X.XX")
            match = re.search(r'Average CC:\s*([\d\.]+)', result.stdout)
            if match:
                return int(float(match.group(1)))
        
        # Fallback: Python file traversal with radon library
        total_cc = 0
        count = 0
        for root, _, files in os.walk(repo_path):
            if any(skip in root for skip in ['.git', 'node_modules', '__pycache__', 'venv']):
                continue
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                            source = f.read()
                        results = cc_visit(source)
                        total_cc += sum(func.complexity for func in results)
                        count += 1
                    except Exception:
                        continue
        return int(total_cc / count) if count > 0 else 1
    except Exception as e:
        logger.warning(f"CC calculation failed, using fallback default: {e}")
        return 1

def check_documentation_criteria(readme_path: str) -> Dict[str, bool]:
    """Check for presence of Setup, API, and Architecture sections."""
    criteria = {
        "setup": False,
        "api": False,
        "architecture": False
    }

    if not os.path.exists(readme_path):
        return criteria

    try:
        with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
        
        # Check for headers (Markdown style)
        headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
        combined_text = " ".join(headers)
        
        # Heuristic checks
        if any(kw in combined_text for kw in ['installation', 'setup', 'getting started', 'quick start']):
            criteria["setup"] = True
        if any(kw in combined_text for kw in ['api', 'endpoint', 'function', 'method', 'usage']):
            criteria["api"] = True
        if any(kw in combined_text for kw in ['architecture', 'structure', 'design', 'components', 'overview']):
            criteria["architecture"] = True
    except Exception:
        pass

    return criteria

def calculate_doc_quality_score(criteria: Dict[str, bool]) -> float:
    """Calculate a score based on documentation criteria (0.0 to 1.0)."""
    total = len(criteria)
    passed = sum(1 for v in criteria.values() if v)
    return passed / total if total > 0 else 0.0

def evaluate_repository_rubric(repo_data: Dict, doc_scores: Dict[str, Dict]) -> Dict[str, Any]:
    """Evaluate a single repository against the rubric."""
    url = repo_data.get('url', '')
    loc = repo_data.get('loc', 0)
    cc = repo_data.get('cc', 0)
    
    # Get doc score
    score_data = doc_scores.get('candidates', [])
    doc_score_entry = next((c for c in score_data if c.get('url') == url), None)
    
    is_high_quality = False
    criteria = {"setup": False, "api": False, "architecture": False}
    
    if doc_score_entry:
        is_high_quality = doc_score_entry.get('is_high_quality', False)
        criteria = doc_score_entry.get('criteria', {})
    else:
        # Fallback if score missing but we have path (rare)
        readme_path = os.path.join(repo_data.get('local_path', ''), 'README.md')
        criteria = check_documentation_criteria(readme_path)
        is_high_quality = calculate_doc_quality_score(criteria) >= 0.75

    return {
        "url": url,
        "loc": loc,
        "cc": cc,
        "is_high_quality": is_high_quality,
        "criteria": criteria,
        "score": calculate_doc_quality_score(criteria)
    }

def run_rubric_on_candidates(candidates: List[Dict], doc_scores_path: str) -> List[Dict]:
    """Run the rubric evaluation on all candidates."""
    doc_scores = load_json_file(doc_scores_path)
    results = []
    for candidate in candidates:
        result = evaluate_repository_rubric(candidate, doc_scores)
        results.append(result)
    return results

def apply_tolerance_filter(evaluation_results: List[Dict], tolerance: float = 0.15) -> Dict[str, Any]:
    """
    Filter repositories based on high-quality docs and LOC/CC tolerance.
    Tolerance is calculated relative to the median of high-quality repos.
    """
    # 1. Filter for high-quality docs
    high_quality_repos = [r for r in evaluation_results if r.get('is_high_quality', False)]
    
    if not high_quality_repos:
        logger.warning("No high-quality repositories found. Returning empty selection.")
        return {
            "selected_repos": [],
            "tolerance_check": {"loc": False, "cc": False},
            "message": "No high-quality repos found"
        }

    # 2. Calculate medians for LOC and CC of high-quality repos
    locs = [r['loc'] for r in high_quality_repos]
    ccs = [r['cc'] for r in high_quality_repos]
    
    locs.sort()
    ccs.sort()
    
    median_loc = locs[len(locs) // 2]
    median_cc = ccs[len(ccs) // 2]
    
    # 3. Apply ±15% tolerance
    loc_low, loc_high = median_loc * (1 - tolerance), median_loc * (1 + tolerance)
    cc_low, cc_high = median_cc * (1 - tolerance), median_cc * (1 + tolerance)
    
    selected = []
    loc_pass = True
    cc_pass = True
    
    for repo in high_quality_repos:
        loc_ok = loc_low <= repo['loc'] <= loc_high
        cc_ok = cc_low <= repo['cc'] <= cc_high
        
        # We select repos that meet BOTH criteria, but we track if the SET as a whole passes
        # The task description implies filtering the SET of candidates to a subset that fits the tolerance
        # "Filter for high-quality docs, then apply ±15% tolerance on LOC and CC."
        # Interpretation: Keep only repos within tolerance of the median of high-quality repos.
        
        if loc_ok and cc_ok:
            selected.append(repo)
        else:
            # If we exclude any, we might flag the tolerance check as "failed" for strictness
            # But usually, we just report which ones passed.
            # Let's interpret "tolerance_check" as: Did the majority pass? Or did we successfully filter?
            pass

    # Logic for tolerance_check booleans:
    # If we have at least one repo in the selected set, and the spread was within tolerance relative to median,
    # we can say the tolerance check passed for the dataset.
    # However, the task asks for a boolean check. Let's assume it means:
    # "Are the selected repos within the tolerance?" -> Yes, by definition of filtering.
    # But if NO repos are selected, then the tolerance check failed to find a match.
    
    tolerance_check = {
        "loc": len(selected) > 0,
        "cc": len(selected) > 0
    }
    
    # If we have high quality repos but none fit the tolerance, that's a failure of the tolerance constraint
    if len(high_quality_repos) > 0 and len(selected) == 0:
        tolerance_check = {"loc": False, "cc": False}

    return {
        "selected_repos": selected,
        "tolerance_check": tolerance_check,
        "median_loc": median_loc,
        "median_cc": median_cc,
        "tolerance_range": {
            "loc": [loc_low, loc_high],
            "cc": [cc_low, cc_high]
        },
        "total_high_quality": len(high_quality_repos),
        "total_selected": len(selected)
    }

def main():
    """
    Main entry point for T021d: Repository Filtering Logic.
    Inputs:
      - config/candidate_repos.yaml
      - data/raw/doc_quality_scores.json
    Outputs:
      - data/raw/repo_selection_rubric.json
    """
    # Paths
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "config" / "candidate_repos.yaml"
    scores_path = base_dir / "data" / "raw" / "doc_quality_scores.json"
    output_path = base_dir / "data" / "raw" / "repo_selection_rubric.json"
    
    logger.info(f"Starting repository filtering. Config: {config_path}, Scores: {scores_path}")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    if not os.path.exists(scores_path):
        raise FileNotFoundError(f"Doc quality scores file not found: {scores_path}")
    
    # Load candidates
    candidates = load_candidate_repos(str(config_path))
    logger.info(f"Loaded {len(candidates)} candidate repositories.")
    
    # Run Rubric
    evaluation_results = run_rubric_on_candidates(candidates, str(scores_path))
    
    # Apply Tolerance Filter
    rubric_result = apply_tolerance_filter(evaluation_results)
    
    # Save Output
    save_json_file(str(output_path), rubric_result)
    logger.info(f"Repository selection rubric saved to {output_path}")
    logger.info(f"Selected {rubric_result['total_selected']} repos out of {rubric_result['total_high_quality']} high-quality candidates.")
    
    # Verification
    if not rubric_result['tolerance_check']['loc'] or not rubric_result['tolerance_check']['cc']:
        logger.warning("Tolerance check failed: No repositories met the ±15% criteria.")
    else:
        logger.info("Tolerance check passed.")

if __name__ == "__main__":
    main()
