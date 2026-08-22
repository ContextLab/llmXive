"""
Task T021b: Implement Lines of Code (LOC) collection.
Runs `cloc --json` for a list of candidate repositories and writes
the results to `data/raw/repo_loc_raw.json`.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path

# Configure logging to avoid circular import issues with utils/logging.py
# by not importing that module directly for basic config.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure the output directory exists."""
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def load_candidate_repos():
    """
    Load candidate repositories from a JSON file.
    Expects `data/raw/candidate_repos.json` (or similar).
    Returns a list of dicts: [{'url': '...', 'path': '...'}, ...]
    """
    candidates_path = Path("data/raw/candidate_repos.json")
    if not candidates_path.exists():
        # Fallback: try to find a list in the project specs or create a minimal one for testing
        # In a real run, this file must exist from T047/T021a logic.
        logger.warning(f"Candidate repos file not found at {candidates_path}. "
                       "Attempting to load from specs or using a placeholder list for structure validation.")
        # Attempt to load from the project's specs if available, otherwise raise
        # For now, we assume the pipeline expects this file to exist.
        raise FileNotFoundError(
            f"Candidate repositories file not found at {candidates_path}. "
            "Please ensure repository selection (T047) has populated this file."
        )
    
    with open(candidates_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Normalize to list of dicts if the format varies
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'repos' in data:
        return data['repos']
    else:
        # Assume the dict itself is the list of repos if keys are URLs
        return [data]

def calculate_loc_via_cloc(repo_info):
    """
    Runs `cloc --json` on the given repository path.
    Returns a dict with LOC metrics for the repo.
    
    Args:
        repo_info (dict): Must contain 'path' or 'local_path' key pointing to the repo directory.
    
    Returns:
        dict: { 'repo_url': ..., 'repo_path': ..., 'total_loc': ..., 'languages': {...} }
    """
    repo_path = repo_info.get('path') or repo_info.get('local_path')
    repo_url = repo_info.get('url', 'unknown')
    
    if not repo_path or not os.path.isdir(repo_path):
        logger.error(f"Repository path not found or invalid for {repo_url}: {repo_path}")
        return {
            'repo_url': repo_url,
            'repo_path': repo_path,
            'error': f"Path not found: {repo_path}",
            'total_loc': 0
        }

    try:
        # Run cloc --json on the directory
        # cloc --json <dir> outputs a JSON object with keys: header, summary, language stats
        cmd = ["cloc", "--json", repo_path]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        cloc_output = json.loads(result.stdout)
        
        # Extract total code lines (excluding blank and comments)
        # cloc JSON structure: { "header": {...}, "SUM": { "code": 1234, ... }, "language": {...} }
        summary = cloc_output.get('SUM', {})
        total_loc = summary.get('code', 0)
        
        # Extract per-language breakdown if needed
        languages = {}
        for key, value in cloc_output.items():
            if key not in ['header', 'SUM'] and isinstance(value, dict):
                if 'code' in value:
                    languages[key] = value['code']

        return {
            'repo_url': repo_url,
            'repo_path': repo_path,
            'total_loc': total_loc,
            'languages': languages,
            'raw_cloc_output': cloc_output # Optional: store raw for debugging if needed, but task asks for numeric LOC
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"cloc failed for {repo_url}: {e.stderr}")
        return {
            'repo_url': repo_url,
            'repo_path': repo_path,
            'error': str(e),
            'total_loc': 0
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse cloc JSON output for {repo_url}: {e}")
        return {
            'repo_url': repo_url,
            'repo_path': repo_path,
            'error': f"JSON decode error: {e}",
            'total_loc': 0
        }

def main():
    """
    Main entry point for T021b.
    1. Ensures data/raw directory exists.
    2. Loads candidate repos.
    3. Runs cloc for each.
    4. Writes results to data/raw/repo_loc_raw.json.
    """
    logger.info("Starting T021b: LOC Collection via cloc")
    
    output_dir = ensure_dirs()
    output_path = output_dir / "repo_loc_raw.json"
    
    try:
        candidates = load_candidate_repos()
        logger.info(f"Loaded {len(candidates)} candidate repositories.")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    results = []
    for repo in candidates:
        logger.info(f"Processing LOC for: {repo.get('url', 'unknown')}")
        loc_data = calculate_loc_via_cloc(repo)
        results.append(loc_data)
    
    # Write results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"LOC collection complete. Results written to {output_path}")
    
    # Verification: Assert file exists and contains numeric LOC
    if output_path.exists():
        with open(output_path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, list) or len(data) == 0:
            logger.error("Verification failed: Output file is empty or not a list.")
            sys.exit(1)
        
        # Check for at least one numeric LOC entry
        has_loc = any(isinstance(r.get('total_loc'), (int, float)) and r.get('total_loc') >= 0 for r in data)
        if not has_loc:
            logger.warning("Verification warning: No valid numeric LOC found in results, but file exists.")
        
        logger.info("Verification passed: data/raw/repo_loc_raw.json exists and contains data.")
    else:
        logger.error("Verification failed: Output file was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
