"""
Script to run metric collection for covariate adjustment (Task T021c).
This script collects LOC and CC metrics from candidate repositories and writes them to data/raw/repo_metrics.json.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from validation import collect_metrics_for_covariates

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for metric collection.
    Reads candidate repos from a config or environment, or uses defaults for testing.
    """
    # Default candidate repos for testing if none provided
    # In production, these should come from a config file or previous selection step
    candidate_repos = os.environ.get('CANDIDATE_REPOS', '').split(',')
    
    if not candidate_repos or (len(candidate_repos) == 1 and candidate_repos[0] == ''):
        # Fallback to a known test repo structure if environment variable is empty
        # This allows the script to run in a test environment
        logger.warning("No candidate repos provided via CANDIDATE_REPOS. Using default test path.")
        # Create a dummy test repo structure for demonstration
        test_repo_path = "data/raw/test_repo"
        os.makedirs(test_repo_path, exist_ok=True)
        
        # Create a sample Python file
        sample_file = os.path.join(test_repo_path, "sample.py")
        with open(sample_file, 'w') as f:
            f.write("""
def hello():
    print("Hello")
    
def calculate(a, b):
    if a > b:
  return a
    else:
  return b
""")
        candidate_repos = [test_repo_path]
    
    output_path = "data/raw/repo_metrics.json"
    
    logger.info(f"Starting metric collection for {len(candidate_repos)} repositories")
    
    try:
        collect_metrics_for_covariates(candidate_repos, output_path)
        logger.info("Metric collection completed successfully.")
    except Exception as e:
        logger.error(f"Metric collection failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()