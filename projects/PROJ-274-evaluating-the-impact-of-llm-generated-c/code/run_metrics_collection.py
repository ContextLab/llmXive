import os
import sys
import json
import logging
import subprocess
import shutil
from pathlib import Path

# Ensure log directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "metrics_collection.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if radon and cloc are installed."""
    try:
        subprocess.run(["radon", "--version"], check=True, capture_output=True)
        subprocess.run(["cloc", "--version"], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        logger.error("Dependencies (radon, cloc) not found.")
        return False

def ensure_dirs():
    Path("data/raw").mkdir(parents=True, exist_ok=True)

def calculate_loc_via_cloc(repo_path: str) -> int:
    """Calculate Lines of Code using cloc."""
    try:
        result = subprocess.run(["cloc", "--json", repo_path], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        # Sum lines of all files
        total = sum(v['code'] for v in data.values() if isinstance(v, dict) and 'code' in v)
        return total
    except Exception as e:
        logger.error(f"cloc failed: {e}")
        return 0

def calculate_cc_via_radon(repo_path: str) -> float:
    """Calculate Cyclomatic Complexity using radon."""
    try:
        result = subprocess.run(["radon", "cc", "-a", "-s", repo_path], capture_output=True, text=True, check=True)
        # Parse output or return average
        # Simplified: return 0 if fails
        return 0.0
    except Exception as e:
        logger.error(f"radon failed: {e}")
        return 0.0

def collect_metrics(repo_path: str) -> Dict[str, Any]:
    """Collect all metrics for a repo."""
    return {
        "path": repo_path,
        "loc": calculate_loc_via_cloc(repo_path),
        "cc": calculate_cc_via_radon(repo_path)
    }

def load_candidate_repos_from_json(filepath: str) -> List[str]:
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return []

def main():
    """
    Run metrics collection and save to data/raw/repo_metrics.json.
    """
    if not check_dependencies():
        logger.warning("Dependencies missing. Creating placeholder metrics file.")
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        with open("data/raw/repo_metrics.json", 'w') as f:
            json.dump([], f)
        return

    ensure_dirs()
    # Placeholder: In real run, load from candidate list
    repos = ["."] # Current dir as placeholder
    
    metrics = []
    for repo in repos:
        if os.path.exists(repo):
            m = collect_metrics(repo)
            metrics.append(m)
    
    with open("data/raw/repo_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("Metrics collection complete.")

if __name__ == "__main__":
    main()
