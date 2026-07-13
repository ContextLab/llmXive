import subprocess
import sys
import os
from pathlib import Path
import hashlib

MOBILEGYM_REPO_URL = "https://github.com/lm-sys/MobileGym.git"
CHECKSUMS_FILE = "data/raw/.checksums.txt"

def get_git_commit_hash(repo_url: str, target_dir: Path) -> str:
    """
    Clones the repository to a temporary location and retrieves the current HEAD commit hash.
    Returns the full 40-character SHA-1 hash.
    """
    try:
        # Clone the repo to a temporary directory to get the hash
        # We use a shallow clone for speed, but we need the commit hash of the tip
        temp_dir = target_dir / ".tmp_mobilegym_clone"
        if temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
        
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Clone the repo
        subprocess.run(
            ["git", "clone", repo_url, str(temp_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Get the commit hash of the current HEAD
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=temp_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        commit_hash = result.stdout.strip()
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        return commit_hash
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone repository or get commit hash: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Error fetching MobileGym repository: {e}")

def create_requirements_txt(target_dir: Path, commit_hash: str) -> Path:
    """
    Creates a requirements.txt file with mobilegym pinned to the specific commit hash.
    """
    requirements_path = target_dir / "requirements.txt"
    
    # Format: git+https://...@<commit_hash>
    # This ensures pip installs exactly that commit
    requirements_content = f"git+{MOBILEGYM_REPO_URL}@{commit_hash}\n"
    
    # Add standard dependencies that might be needed for the project
    # Based on the task list, we might need ruff, black, etc., but keeping it minimal
    # to just satisfy the "Pin mobilegym" requirement first.
    # We can add others if they are standard for the project.
    standard_deps = [
        "numpy",
        "pandas",
        "scikit-learn",
        "matplotlib",
        "pytest",
        "ruff",
        "black"
    ]
    
    for dep in standard_deps:
        requirements_content += f"{dep}\n"
    
    requirements_path.write_text(requirements_content)
    return requirements_path

def write_checksums_file(target_dir: Path, commit_hash: str, repo_url: str) -> Path:
    """
    Writes the commit hash and repo URL to the checksums file for reproducibility.
    Format: <repo_name>:<commit_hash>
    """
    checksums_path = target_dir / CHECKSUMS_FILE
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure the directory exists
    checksums_path.write_text(f"mobilegym:{commit_hash}\n")
    return checksums_path

def main():
    """
    Main entry point to initialize the Python project requirements.
    1. Fetches MobileGym commit hash.
    2. Creates requirements.txt with pinned version.
    3. Writes checksums to data/raw/.checksums.txt.
    """
    # Determine project root (assuming this script is in code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    print(f"Project root: {project_root}")
    
    # 1. Get commit hash
    print("Fetching MobileGym commit hash...")
    try:
        commit_hash = get_git_commit_hash(MOBILEGYM_REPO_URL, project_root)
        print(f"Retrieved commit hash: {commit_hash}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # 2. Create requirements.txt
    print("Creating requirements.txt...")
    req_path = create_requirements_txt(project_root, commit_hash)
    print(f"Created: {req_path}")
    
    # 3. Write checksums
    print("Writing checksums...")
    checksum_path = write_checksums_file(project_root, commit_hash, MOBILEGYM_REPO_URL)
    print(f"Created: {checksum_path}")
    
    print("Project initialization complete.")

if __name__ == "__main__":
    main()
