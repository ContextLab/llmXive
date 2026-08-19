import os
import sys
import json
import logging
import subprocess
import shutil
from pathlib import Path

# Configure logging to avoid circular import issues seen in execution logs
# by ensuring logging is set up before any other logging calls
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if radon and cloc are installed and available."""
    missing = []
    
    # Check radon
    try:
        subprocess.run(['radon', '--version'], capture_output=True, check=True)
        logger.info("radon is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("radon")
        logger.warning("radon is not installed. Please install it via pip: pip install radon")
    
    # Check cloc
    try:
        subprocess.run(['cloc', '--version'], capture_output=True, check=True)
        logger.info("cloc is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("cloc")
        logger.warning("cloc is not installed. Please install it via system package manager (e.g., apt install cloc)")
    
    if missing:
        raise RuntimeError(f"Missing required dependencies: {', '.join(missing)}")
    
    return True

def ensure_dirs():
    """Ensure the output directory exists."""
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def calculate_loc_via_cloc(repo_path):
    """
    Calculate Lines of Code (LOC) for a repository using cloc.
    
    Args:
        repo_path: Path to the repository directory
        
    Returns:
        int: Total lines of code (excluding blanks and comments)
    """
    if not os.path.isdir(repo_path):
        raise FileNotFoundError(f"Repository directory not found: {repo_path}")
    
    try:
        result = subprocess.run(
            ['cloc', '--json', repo_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        data = json.loads(result.stdout)
        
        # cloc returns a structure like:
        # {
        #   "header": {...},
        #   "SUM": {
        #     "nCode": 12345,
        #     ...
        #   }
        # }
        if "SUM" in data and "nCode" in data["SUM"]:
            return data["SUM"]["nCode"]
        else:
            logger.warning(f"Could not find nCode in cloc output for {repo_path}")
            return 0
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running cloc on {repo_path}: {e.stderr}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing cloc JSON output for {repo_path}: {e}")
        raise

def calculate_cc_via_radon(repo_path):
    """
    Calculate Cyclomatic Complexity (CC) for a repository using radon.
    
    Uses: radon cc -a -s <repo_path>
    -a: aggregate (average)
    -s: sum of all complexities (we use the sum as the repo-level metric)
    
    Args:
        repo_path: Path to the repository directory
        
    Returns:
        float: Sum of cyclomatic complexities (or average if preferred)
    """
    if not os.path.isdir(repo_path):
        raise FileNotFoundError(f"Repository directory not found: {repo_path}")
    
    try:
        # Run radon cc with aggregate and summary flags
        # We capture the output and parse the summary line
        result = subprocess.run(
            ['radon', 'cc', '-a', '-s', repo_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        output = result.stdout
        lines = output.strip().split('\n')
        
        # The last line usually contains the summary
        # Format: "Total Average: <avg> (count)" or similar
        # We look for the line that contains "Average" and extract the value
        avg_cc = None
        total_cc = None
        
        for line in lines:
            if 'Average' in line:
                # Extract the number before the parenthesis
                import re
                match = re.search(r'Average: ([\d.]+)', line)
                if match:
                    avg_cc = float(match.group(1))
            elif 'Total' in line and 'Average' not in line:
                # Some versions output "Total: X"
                import re
                match = re.search(r'Total: ([\d.]+)', line)
                if match:
                    total_cc = float(match.group(1))
        
        # If we have total, use it; otherwise use average * estimated count
        # For robustness, we'll use the average if total is not available
        # But the task asks for a metric per repo, so we return the average
        # which is more comparable across repos of different sizes
        if avg_cc is not None:
            return avg_cc
        elif total_cc is not None:
            return total_cc
        else:
            logger.warning(f"Could not parse radon output for {repo_path}")
            logger.debug(f"Output was: {output}")
            return 0.0
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running radon on {repo_path}: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing radon output for {repo_path}: {e}")
        raise

def collect_metrics(repo_paths):
    """
    Collect LOC and CC metrics for a list of repository paths.
    
    Args:
        repo_paths: List of paths to repositories
        
    Returns:
        dict: Metrics data structure
    """
    metrics = {
        "repos": [],
        "count": len(repo_paths),
        "status": "complete"
    }
    
    failed_repos = []
    
    for repo_path in repo_paths:
        repo_name = os.path.basename(repo_path)
        logger.info(f"Collecting metrics for {repo_name} at {repo_path}")
        
        try:
            loc = calculate_loc_via_cloc(repo_path)
            cc = calculate_cc_via_radon(repo_path)
            
            metrics["repos"].append({
                "repo_path": repo_path,
                "repo_name": repo_name,
                "loc": loc,
                "cc": cc
            })
            
            logger.info(f"  LOC: {loc}, CC: {cc}")
            
        except Exception as e:
            logger.error(f"Failed to collect metrics for {repo_name}: {e}")
            failed_repos.append({
                "repo_path": repo_path,
                "repo_name": repo_name,
                "error": str(e)
            })
            metrics["status"] = "partial"
    
    if failed_repos:
        metrics["failed"] = failed_repos
        logger.warning(f"Failed to collect metrics for {len(failed_repos)} repositories")
    
    return metrics

def main():
    """Main entry point for metric collection."""
    logger.info("Starting metric collection for covariate adjustment")
    
    # Check dependencies first
    try:
        check_dependencies()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Load candidate repos
    candidate_file = Path("data/raw/candidate_repos.json")
    if not candidate_file.exists():
        logger.error(f"Candidate repos file not found: {candidate_file}")
        logger.error("Please run T021a first to generate candidate_repos.json")
        sys.exit(1)
    
    try:
        with open(candidate_file, 'r') as f:
            candidate_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing candidate_repos.json: {e}")
        sys.exit(1)
    
    if "candidates" not in candidate_data:
        logger.error("candidate_repos.json does not contain 'candidates' key")
        sys.exit(1)
    
    repo_paths = candidate_data["candidates"]
    logger.info(f"Found {len(repo_paths)} candidate repositories")
    
    # Ensure output directory exists
    ensure_dirs()
    
    # Collect metrics
    metrics = collect_metrics(repo_paths)
    
    # Save results
    output_file = Path("data/raw/repo_metrics.json")
    try:
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics saved to {output_file}")
    except IOError as e:
        logger.error(f"Failed to write metrics to {output_file}: {e}")
        sys.exit(1)
    
    # Verify output
    if not output_file.exists():
        logger.error("Output file was not created")
        sys.exit(1)
    
    logger.info("Metric collection completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())