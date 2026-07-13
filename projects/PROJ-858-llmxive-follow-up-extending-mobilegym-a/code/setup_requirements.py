import os
import subprocess
import sys
import hashlib
from datetime import datetime
from utils.logging import get_task_logger, log_task_start, log_task_complete, log_error

logger = get_task_logger(__name__)

REPO_URL = "https://github.com/llmXive/mobilegym.git"
REQUIREMENTS_PATH = "requirements.txt"
CHECKSUM_PATH = "data/raw/.checksums.txt"

def get_git_commit_hash(repo_url: str) -> str:
    """
    Clones (or fetches into) the repository and returns the current HEAD commit hash.
    Uses a shallow clone for speed, but ensures we get the actual commit hash.
    """
    logger.info(f"Fetching repository to determine commit hash: {repo_url}")
    
    # Create a temporary directory for the clone
    temp_dir = "data/raw/.temp_mobilegym_clone"
    os.makedirs(os.path.dirname(temp_dir), exist_ok=True)
    
    # Remove existing clone if present to ensure fresh state
    if os.path.exists(temp_dir):
        subprocess.run(["rm", "-rf", temp_dir], check=True)

    try:
        # Clone the repository (shallow to save time)
        # We fetch the full history for the commit hash to be reliable in some edge cases, 
        # but shallow is usually fine for HEAD.
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Get the commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=temp_dir,
            check=True,
            capture_output=True,
            text=True
        )
        commit_hash = result.stdout.strip()
        logger.info(f"Retrieved commit hash: {commit_hash}")
        return commit_hash

    except subprocess.CalledProcessError as e:
        log_error(logger, "Failed to fetch repository or get commit hash", e)
        raise RuntimeError(f"Failed to fetch repository {repo_url}: {e}")
    finally:
        # Cleanup temp directory
        if os.path.exists(temp_dir):
            subprocess.run(["rm", "-rf", temp_dir], check=True)

def generate_requirements_txt(commit_hash: str) -> str:
    """
    Generates the content for requirements.txt, pinning mobilegym to the specific commit.
    """
    content = f"""# MobileGym Research Pipeline Requirements
# Generated: {datetime.now().isoformat()}
# Source: {REPO_URL}

# Core dependency: MobileGym pinned to specific commit for reproducibility
git+{REPO_URL}@{commit_hash}#egg=mobilegym

# Standard dependencies for the pipeline
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
pyyaml>=6.0
pytest>=7.0.0
ruff>=0.1.0
black>=23.0.0
"""
    return content

def write_checksum_file(commit_hash: str) -> None:
    """
    Writes the commit hash to data/raw/.checksums.txt, overwriting the placeholder.
    """
    os.makedirs(os.path.dirname(CHECKSUM_PATH), exist_ok=True)
    
    content = f"""# MobileGym Checksums
# Generated: {datetime.now().isoformat()}
# Repository: {REPO_URL}
mobilegym={commit_hash}
"""
    
    with open(CHECKSUM_PATH, "w") as f:
        f.write(content)
    
    logger.info(f"Wrote checksum file to {CHECKSUM_PATH}")

def main():
    log_task_start(logger, "T002", "Initialize Python project with requirements.txt")
    try:
        # 1. Fetch the real commit hash
        commit_hash = get_git_commit_hash(REPO_URL)
        
        # 2. Generate and write requirements.txt
        req_content = generate_requirements_txt(commit_hash)
        with open(REQUIREMENTS_PATH, "w") as f:
            f.write(req_content)
        logger.info(f"Created {REQUIREMENTS_PATH}")
        
        # 3. Update the checksum file
        write_checksum_file(commit_hash)
        
        log_task_complete(logger, "T002")
        return True
    except Exception as e:
        log_error(logger, "Task T002 failed", e)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)