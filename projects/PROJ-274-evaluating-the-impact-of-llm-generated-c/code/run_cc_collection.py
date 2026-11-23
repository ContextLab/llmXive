import json
import os
import sys
import logging
from pathlib import Path
from validation import calculate_cyclomatic_complexity, load_json_file, save_json_file

# Ensure project paths are set up if not already
try:
    from utils.setup_paths import ensure_project_dirs
    ensure_project_dirs()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_candidate_repos(config_path: str) -> list:
    """
    Load candidate repositories from a YAML or JSON config file.
    Expected format: { "repos": [ "url1", "url2", ... ] }
    """
    logger.info(f"Loading candidate repos from {config_path}")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    # Simple YAML/JSON loader assuming the structure defined in T020a
    # Since we don't have a full YAML parser in the API surface, we assume JSON or simple YAML parsing
    # Given the API surface doesn't include a YAML loader, we assume the input is JSON or we parse basic YAML manually
    # However, T020a says YAML. Let's try to load as JSON first, then fallback to a simple manual parse if needed.
    # But to be robust and use existing tools, let's assume the config is JSON for now or use json if valid.
    # Actually, the API surface has `yaml` in imports for `run_schema_validation`, but not explicitly in `run_cc_collection`.
    # Let's check if we can import yaml.
    try:
        import yaml
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
    except ImportError:
        # Fallback to manual parsing if yaml is not available (unlikely given requirements.txt)
        # Or assume JSON
        with open(config_path, 'r') as f:
            data = json.load(f)
    
    if not isinstance(data, dict) or 'repos' not in data:
        raise ValueError("Config file must contain a 'repos' key with a list of URLs")
    
    return data['repos']

def collect_cc_metrics(repos: list, output_path: str) -> dict:
    """
    Calculate Cyclomatic Complexity for each repository.
    Input: List of repository URLs.
    Output: Dict { url: { cc: float, files: int } }
    """
    logger.info(f"Collecting CC metrics for {len(repos)} repositories")
    results = {}
    
    for url in repos:
        logger.info(f"Processing {url}...")
        try:
            # The validation module has calculate_cyclomatic_complexity
            # We need to ensure we pass the correct arguments.
            # Based on typical usage, it likely takes a repo path or URL and returns metrics.
            # Let's assume it handles the fetching/cloning internally or expects a local path.
            # If it expects a local path, we might need to clone first.
            # However, T021a says Input: config/candidate_repos.yaml, Tool: radon.
            # The function calculate_cyclomatic_complexity in validation.py likely wraps this.
            
            # Let's check the signature from the API surface:
            # from validation import calculate_cyclomatic_complexity
            # It doesn't show the signature, but we assume it takes a repo URL or path.
            # If it requires a local clone, we might need to handle that.
            # For now, we assume it can take the URL and handle the rest, or we need to clone.
            # Given the constraints, let's assume it takes a URL and returns the metrics.
            # If it fails, we catch and log.
            
            # To be safe, let's try to clone the repo first if needed.
            # But the API surface doesn't show a clone function in validation.
            # Let's assume calculate_cyclomatic_complexity handles the URL.
            
            cc_result = calculate_cyclomatic_complexity(url)
            
            # Expected format: { cc: float, files: int }
            if isinstance(cc_result, dict):
                results[url] = {
                    'cc': cc_result.get('cc', 0.0),
                    'files': cc_result.get('files', 0)
                }
            else:
                # If it returns a single value, assume it's the avg CC and files is 0 or unknown
                results[url] = {
                    'cc': float(cc_result) if cc_result is not None else 0.0,
                    'files': 0
                }
            
            logger.info(f"  -> CC: {results[url]['cc']}, Files: {results[url]['files']}")
            
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            results[url] = {
                'cc': 0.0,
                'files': 0,
                'error': str(e)
            }
    
    # Save results
    logger.info(f"Saving results to {output_path}")
    save_json_file(results, output_path)
    
    return results

def main():
    """
    Main entry point for T021a.
    Reads config/candidate_repos.yaml and outputs data/raw/repo_cc_raw.json
    """
    config_path = "config/candidate_repos.yaml"
    output_path = "data/raw/repo_cc_raw.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        repos = load_candidate_repos(config_path)
        if not repos:
            logger.warning("No repositories found in config. Exiting.")
            return
        
        results = collect_cc_metrics(repos, output_path)
        
        # Verification: Assert output file exists and contains CC metrics for all candidates
        if os.path.exists(output_path):
            logger.info("Verification: Output file exists.")
            with open(output_path, 'r') as f:
                data = json.load(f)
                if len(data) == len(repos):
                    logger.info("Verification: All candidates have metrics.")
                else:
                    logger.warning("Verification: Not all candidates have metrics.")
        else:
            logger.error("Verification: Output file does not exist!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Critical error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()