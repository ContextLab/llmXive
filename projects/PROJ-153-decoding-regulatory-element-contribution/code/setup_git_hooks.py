import os
import subprocess
import sys
from pathlib import Path

def run_command(command: list, cwd: Path = None) -> bool:
    """Execute a shell command and return True if successful."""
    try:
        subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print(f"stderr: {e.stderr}")
        print(f"stdout: {e.stdout}")
        return False

def check_git_lfs_installed() -> bool:
    """Check if git-lfs is installed and available."""
    try:
        result = subprocess.run(["git", "lfs", "version"], capture_output=True, text=True, check=True)
        print(f"Git LFS installed: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Git LFS is not installed or not in PATH.")
        print("Install via: apt-get install git-lfs (Debian/Ubuntu) or brew install git-lfs (macOS)")
        return False

def install_git_lfs() -> bool:
    """Initialize git-lfs in the current repository."""
    print("Initializing Git LFS...")
    return run_command(["git", "lfs", "install"])

def setup_lfs_tracking() -> bool:
    """Ensure .gitattributes is present and tracked."""
    root = Path.cwd()
    gitattributes_path = root / ".gitattributes"
    
    if not gitattributes_path.exists():
        print(f"Error: .gitattributes not found at {gitattributes_path}")
        print("Please ensure the .gitattributes file is created before running this hook setup.")
        return False

    # Check if .gitattributes is already tracked by LFS
    try:
        result = subprocess.run(
            ["git", "lfs", "ls-files", "--name-only"],
            capture_output=True, text=True, check=True
        )
        tracked_files = result.stdout.strip().split('\n')
        if ".gitattributes" in tracked_files:
            print(".gitattributes is already tracked by LFS.")
        else:
            print("Adding .gitattributes to LFS tracking...")
            # We force add it to ensure it's tracked if it was ignored previously
            run_command(["git", "lfs", "track", ".gitattributes"], cwd=root)
            # Stage the change
            run_command(["git", "add", ".gitattributes"], cwd=root)
    except subprocess.CalledProcessError:
        print("Warning: Could not verify LFS tracking status for .gitattributes.")

    return True

def create_pre_push_hook() -> bool:
    """Create a pre-push hook to warn about large files not in LFS."""
    root = Path.cwd()
    hooks_dir = root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    hook_path = hooks_dir / "pre-push"
    hook_script = '''#!/bin/bash
    # Pre-push hook: Verify large files are tracked by Git LFS

    # List of patterns that should be tracked by LFS
    LFS_PATTERNS=(
        "*.fastq.gz" "*.fq.gz"
        "*.bam" "*.cram"
        "*.bed" "*.bw" "*.bigwig"
        "*.cool" "*.h5"
        "*.pdf" "*.csv" "*.tsv"
        "*.png" "*.svg"
    )

    # Get list of files being pushed
    files=$(git diff-tree --no-commit-id --name-only -r "$1" "$2" 2>/dev/null)

    if [ -z "$files" ]; then
        exit 0
    fi

    large_files_found=0
    for file in $files; do
        for pattern in "${LFS_PATTERNS[@]}"; do
            if [[ "$file" == $pattern ]]; then
                # Check if file is tracked by LFS
                if ! git lfs ls-files | grep -q "$file"; then
                    echo "ERROR: Large file '$file' matches pattern '$pattern' but is NOT tracked by Git LFS."
                    echo "Please run 'git lfs track' and commit the .gitattributes file."
                    large_files_found=1
                fi
                break
            fi
        done
    done

    if [ $large_files_found -eq 1 ]; then
        echo ""
        echo "Push rejected. One or more large files are not tracked by Git LFS."
        echo "To fix this:"
        echo "1. Ensure .gitattributes is correct and committed."
        echo "2. Run: git lfs track <file_pattern>"
        echo "3. git add .gitattributes"
        echo "4. git commit -m 'Track large files'"
        exit 1
    fi

    exit 0
    '''

    with open(hook_path, 'w') as f:
        f.write(hook_script)
    
    # Make executable
    os.chmod(hook_path, 0o755)
    print(f"Pre-push hook created at {hook_path}")
    return True

def main():
    """Main entry point for Git LFS setup."""
    print("=== Git LFS Setup for PROJ-153 ===")
    
    # Check if we are in a git repository
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Not a git repository. Please initialize git first.")
        sys.exit(1)

    if not check_git_lfs_installed():
        sys.exit(1)

    if not install_git_lfs():
        print("Warning: Git LFS initialization failed, but continuing...")

    if not setup_lfs_tracking():
        print("Warning: LFS tracking setup failed.")
    
    if not create_pre_push_hook():
        print("Warning: Pre-push hook creation failed.")

    print("=== Git LFS Setup Complete ===")
    print("Next steps:")
    print("1. Commit the .gitattributes file: git add .gitattributes && git commit -m 'Setup LFS tracking'")
    print("2. Push the repository: git push")

if __name__ == "__main__":
    main()
