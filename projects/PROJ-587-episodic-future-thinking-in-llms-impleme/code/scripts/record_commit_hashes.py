"""
Script to record specific commit hashes for ALFWorld and TextWorld datasets.

This script fetches the current HEAD commit hashes for the official ALFWorld
and TextWorld repositories and records them to data/commit_hashes.txt.

This satisfies Constitution Principle I by ensuring dataset provenance is
captured at the time of data processing.
"""
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configuration: Official repositories
REPOSITORIES = {
    "ALFWorld": "https://github.com/alfworld/alfworld.git",
    "TextWorld": "https://github.com/microsoft/TextWorld.git",
}

# Output file path relative to project root
OUTPUT_FILENAME = "commit_hashes.txt"

def get_commit_hash(repo_url: str, temp_dir: Path) -> str:
    """
    Clones (or fetches if exists) the repository and returns the HEAD commit hash.
    
    Args:
        repo_url: URL of the git repository
        temp_dir: Directory to clone/fetch the repo into
    
    Returns:
        The short commit hash (7 characters) of the HEAD
    
    Raises:
        subprocess.CalledProcessError: If git operations fail
    """
    repo_name = repo_url.split("/")[-1].replace(".git", "")
    repo_path = temp_dir / repo_name

    if not repo_path.exists():
        print(f"Cloning {repo_name}...")
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(repo_path)],
            check=True,
            capture_output=True,
        )
    else:
        print(f"Fetching latest for {repo_name}...")
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "reset", "--hard", "origin/HEAD"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

    # Get the commit hash
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()[:7]

def main():
    """Main entry point for recording commit hashes."""
    # Determine project root (parent of 'code')
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent
    data_dir = project_root / "data"

    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / OUTPUT_FILENAME

    print(f"Recording commit hashes to: {output_path}")
    print("-" * 50)

    hashes = {}
    failures = []

    for name, url in REPOSITORIES.items():
        try:
            # Use a temporary directory for cloning
            temp_dir = Path("/tmp/llmXive_repo_cache")
            temp_dir.mkdir(exist_ok=True)
            
            commit_hash = get_commit_hash(url, temp_dir)
            hashes[name] = commit_hash
            print(f"✓ {name}: {commit_hash}")
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to fetch {name}: {e.stderr.decode()}"
            print(f"✗ {name}: {error_msg}")
            failures.append((name, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error for {name}: {str(e)}"
            print(f"✗ {name}: {error_msg}")
            failures.append((name, error_msg))

    print("-" * 50)

    if failures:
        print(f"\n⚠️  {len(failures)} repository(s) failed to fetch.")
        print("Writing partial results. Please check the errors above.")
    
    # Write results to file
    timestamp = datetime.utcnow().isoformat() + "Z"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Dataset Commit Hashes\n")
        f.write(f"# Generated: {timestamp}\n")
        f.write(f"# Constitution Principle I: Reproducibility\n")
        f.write(f"#\n")
        f.write(f"# Format: <Dataset Name>: <Commit Hash>\n")
        f.write(f"#\n")
        
        for name, hash_val in hashes.items():
            f.write(f"{name}: {hash_val}\n")
        
        if failures:
            f.write(f"\n# FAILED:\n")
            for name, err in failures:
                f.write(f"# {name}: {err}\n")

    print(f"\n✓ Successfully wrote {len(hashes)} hash(es) to {output_path.relative_to(project_root)}")
    
    if failures:
        sys.exit(1)
    else:
        print("✓ All repositories processed successfully.")

if __name__ == "__main__":
    main()