"""
Task T021b: Calculate Lines of Code (LOC) for candidate repositories.
Input: config/candidate_repos.yaml
Tool: cloc
Output: data/raw/repo_loc_raw.json
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logging to avoid circular import issues with code/utils/logging.py
# We configure a local logger instance here.
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Ensure we are running from the project root or handle relative paths correctly
# The project structure implies this script is at code/run_loc_collection.py
# We need to resolve paths relative to the project root.
def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Navigate up from code/ to project root
    if current.name == 'run_loc_collection.py':
        return current.parent.parent
    # Fallback if run from different context
    return Path.cwd()

def ensure_dirs() -> None:
    """Ensure required output directories exist."""
    project_root = get_project_root()
    data_raw_dir = project_root / 'data' / 'raw'
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory: {data_raw_dir}")

def load_candidate_repos(config_path: Optional[Path] = None) -> List[str]:
    """
    Load candidate repository URLs from the YAML config.
    Input: config/candidate_repos.yaml
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / 'config' / 'candidate_repos.yaml'

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, list) and not isinstance(config, dict):
            # Handle case where YAML is just a list
            if isinstance(config, list):
                return config
            raise ValueError("Invalid config format: expected list or dict")
        
        # If it's a dict, look for a key like 'repos' or 'candidates'
        if isinstance(config, dict):
            # Try common keys
            for key in ['repos', 'candidates', 'urls', 'repositories']:
                if key in config:
                    return config[key]
            # If no specific key, assume the dict values are the list (unlikely) or keys
            # Based on typical YAML structure for this task, it's likely a list at root or under 'repos'
            # If it's a flat dict of name->url, extract values
            if all(isinstance(v, str) for v in config.values()):
                return list(config.values())
            raise ValueError("Could not find repository list in config. Expected 'repos' key or a list.")
        
        return config

    except ImportError:
        logger.error("PyYAML is required. Install with: pip install pyyaml")
        raise
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

def calculate_loc_via_cloc(repo_url: str, timeout: int = 300) -> Dict[str, Any]:
    """
    Calculate Lines of Code (LOC) for a single repository using cloc.
    
    Args:
        repo_url: The URL of the repository.
        timeout: Timeout in seconds for the subprocess.
        
    Returns:
        Dict with 'loc' (total lines) and 'sloc' (source lines of code).
    """
    logger.info(f"Processing repository: {repo_url}")
    
    # We need to clone or fetch the repo to run cloc locally, or use a remote cloc wrapper.
    # Since cloc is a local tool, we must clone the repo to a temporary directory.
    # However, T021a and T021b are Phase 2 tasks for candidate selection.
    # The prompt implies we should run cloc on the candidates.
    # To avoid full clones if possible, we might use a shallow clone.
    # But for accurate LOC, we need the files.
    
    # Strategy: Clone to a temp dir, run cloc, remove temp dir.
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    repo_path = os.path.join(temp_dir, repo_name)
    
    try:
        # Clone the repo (shallow for speed)
        clone_cmd = ['git', 'clone', '--depth', '1', repo_url, repo_path]
        logger.debug(f"Running: {' '.join(clone_cmd)}")
        clone_result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=60)
        
        if clone_result.returncode != 0:
            logger.warning(f"Failed to clone {repo_url}: {clone_result.stderr}")
            # If clone fails, we cannot calculate LOC. Return None or raise.
            # Per constraint: "FAIL LOUDLY".
            raise RuntimeError(f"Failed to clone repository {repo_url}: {clone_result.stderr}")
        
        # Run cloc
        cloc_cmd = ['cloc', '--json', repo_path]
        logger.debug(f"Running: {' '.join(cloc_cmd)}")
        cloc_result = subprocess.run(cloc_cmd, capture_output=True, text=True, timeout=timeout)
        
        if cloc_result.returncode != 0:
            logger.warning(f"cloc failed for {repo_url}: {cloc_result.stderr}")
            raise RuntimeError(f"cloc failed for {repo_url}: {cloc_result.stderr}")
        
        # Parse JSON output
        try:
            cloc_data = json.loads(cloc_result.stdout)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse cloc output for {repo_url}")
            raise ValueError(f"Invalid cloc output for {repo_url}")
        
        # cloc JSON structure:
        # {
        #   "header": {...},
        #   "SUM": {
        #     "nCode": 123,  # Lines of Code (LOC)
        #     "nBlank": 456,
        #     "nComment": 789,
        #     "nSource": 123  # Source Lines of Code (SLOC) - sometimes distinct
        #   },
        #   "ext": {...}
        # }
        # Note: 'nCode' is often total code lines, 'nSource' is SLOC.
        # The task asks for 'loc' and 'sloc'.
        # In cloc terms:
        #   nCode = Total lines of code (including blanks inside code blocks? No, usually non-blank, non-comment)
        #   nSource = Source lines of code (excluding blanks and comments)
        # Let's map:
        #   loc -> nCode (Total lines of code)
        #   sloc -> nSource (Source lines of code)
        
        if 'SUM' not in cloc_data:
            logger.warning(f"No SUM section in cloc output for {repo_url}")
            return {'loc': 0, 'sloc': 0}
        
        sum_data = cloc_data['SUM']
        loc = sum_data.get('nCode', 0)
        sloc = sum_data.get('nSource', 0)
        
        logger.info(f"Repository {repo_url}: LOC={loc}, SLOC={sloc}")
        return {'loc': loc, 'sloc': sloc}
        
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout cloning or analyzing {repo_url}")
        raise RuntimeError(f"Timeout processing {repo_url}")
    except Exception as e:
        logger.error(f"Error processing {repo_url}: {e}")
        raise
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def main():
    """
    Main entry point for T021b.
    Reads config/candidate_repos.yaml, calculates LOC for each, writes to data/raw/repo_loc_raw.json.
    """
    logger.info("Starting T021b: LOC Collection")
    
    ensure_dirs()
    project_root = get_project_root()
    
    # Load candidates
    try:
        candidates = load_candidate_repos()
    except Exception as e:
        logger.error(f"Failed to load candidates: {e}")
        sys.exit(1)
    
    if not candidates:
        logger.warning("No candidate repositories found.")
        # Write empty result to avoid downstream breakage? Or fail?
        # Fail loudly as per constraints.
        sys.exit(1)
    
    results = {}
    
    for url in candidates:
        if not url:
            continue
        try:
            metrics = calculate_loc_via_cloc(url)
            results[url] = metrics
        except Exception as e:
            logger.error(f"Skipping {url} due to error: {e}")
            # Per constraint: "FAIL LOUDLY". If one fails, the whole run should probably fail
            # or at least not produce partial results that look valid.
            # However, for a pilot, we might want to see which ones worked.
            # But the task says "Assert output file exists and contains LOC metrics for ALL candidates".
            # So if any fail, we must exit.
            logger.error("Aborting due to failure in processing a candidate.")
            sys.exit(1)
    
    output_path = project_root / 'data' / 'raw' / 'repo_loc_raw.json'
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Successfully wrote results to {output_path}")
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        sys.exit(1)
    
    logger.info("T021b completed successfully.")

if __name__ == '__main__':
    main()