"""
Setup Git LFS hooks for large file tracking in the llmXive project.

This script configures Git LFS for the repository to track large data files
(raw FASTQ, BAM, bigWig, etc.) while keeping the Git history lightweight.

Usage:
    python code/setup_git_hooks.py
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"stderr: {result.stderr}")
            return False
        if result.stdout:
            print(result.stdout.strip())
        return True
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def check_git_lfs_installed():
    """Check if Git LFS is installed."""
    result = subprocess.run(
        ["git", "lfs", "version"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0

def install_git_lfs():
    """Install Git LFS if not already installed."""
    print("Installing Git LFS...")
    if not run_command("git lfs install"):
        print("Failed to install Git LFS. Please install it manually:")
        print("  - macOS: brew install git-lfs")
        print("  - Linux: apt-get install git-lfs")
        print("  - Windows: Download from https://git-lfs.github.com/")
        return False
    return True

def setup_lfs_tracking():
    """Configure Git LFS to track specific file patterns."""
    patterns = [
        "*.fastq",
        "*.fastq.gz",
        "*.bam",
        "*.cram",
        "*.bigwig",
        "*.bw",
        "*.cool",
        "*.mcool",
        "*.hic",
        "*.tsv.gz",
        "*.csv.gz",
        "*.bed.gz",
        "*.gz",
        "*.tar",
        "*.tar.gz",
        "*.zip",
        "data/raw/**/*",
        "data/processed/**/*",
        "results/**/*"
    ]
    
    print("Configuring Git LFS tracking patterns...")
    for pattern in patterns:
        # Use git lfs track with --filename to avoid .gitattributes conflicts
        if not run_command(f'git lfs track "{pattern}"'):
            print(f"Warning: Could not track pattern {pattern}")
    
    # Commit .gitattributes if it changed
    if run_command("git add .gitattributes"):
        if run_command("git status --porcelain .gitattributes"):
            print("Created/updated .gitattributes file")
        else:
            print("No changes to .gitattributes")
    else:
        print("Warning: Could not stage .gitattributes")
    
    return True

def create_pre_push_hook():
    """Create a pre-push hook to warn about large untracked files."""
    hooks_dir = Path(".git/hooks")
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    pre_push_script = hooks_dir / "pre-push"
    
    hook_content = '''#!/bin/bash
# Pre-push hook to check for large untracked files
# This helps prevent accidentally pushing large files without LFS

LARGE_FILE_THRESHOLD=10000000  # 10MB

echo "Checking for large files that should be tracked by Git LFS..."

# Find files larger than threshold that aren't tracked by LFS
large_files=$(git ls-files --others --exclude-standard | while read file; do
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    if [ "$size" -gt $LARGE_FILE_THRESHOLD ]; then
  echo "$file ($((size/1024/1024))MB)"
    fi
done)

if [ -n "$large_files" ]; then
    echo "WARNING: The following large files are not tracked by Git LFS:"
    echo "$large_files"
    echo ""
    echo "Please track them with: git lfs track <filename>"
    echo "Or add them to .gitignore if they should not be versioned."
    echo ""
    echo "To skip this check, set GIT_LFS_SKIP_PUSH_CHECK=1"
    if [ -z "$GIT_LFS_SKIP_PUSH_CHECK" ]; then
  exit 1
    fi
fi

echo "Large file check passed."
exit 0
'''
    
    with open(pre_push_script, "w") as f:
        f.write(hook_content)
    
    # Make executable
    if sys.platform != "win32":
        os.chmod(pre_push_script, 0o755)
    
    print(f"Created pre-push hook at {pre_push_script}")
    return True

def main():
    """Main entry point for Git LFS setup."""
    print("=" * 60)
    print("Setting up Git LFS for llmXive project")
    print("=" * 60)
    
    # Check if we're in a git repository
    if not run_command("git rev-parse --is-inside-work-tree"):
        print("Error: Not a git repository. Please initialize git first.")
        sys.exit(1)
    
    # Check/install Git LFS
    if not check_git_lfs_installed():
        print("Git LFS not found. Attempting to install...")
        if not install_git_lfs():
            print("Failed to install Git LFS. Please install manually and re-run.")
            sys.exit(1)
    else:
        print("Git LFS is already installed.")
    
    # Setup tracking patterns
    if not setup_lfs_tracking():
        print("Warning: Some tracking patterns could not be set up.")
    
    # Create pre-push hook
    if not create_pre_push_hook():
        print("Warning: Could not create pre-push hook.")
    
    print("=" * 60)
    print("Git LFS setup complete!")
    print("Next steps:")
    print("  1. Add large files to git: git add data/raw/...")
    print("  2. Commit: git commit -m 'Add raw data'")
    print("  3. Push: git push (will trigger pre-push check)")
    print("=" * 60)

if __name__ == "__main__":
    main()