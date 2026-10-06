"""
Git Repository Initialization Module.

This module handles the initialization of the Git repository for the project.
It ensures the repository is created, performs an initial commit to establish history,
and verifies the state of the repository.
"""
import os
import subprocess
import sys
from pathlib import Path
import logging

# Import the shared logger utility if available, otherwise configure local logger
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback if utils.logger is not yet imported in this context
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

def initialize_git_repo(project_root: Path) -> bool:
    """
    Initialize a git repository in the specified project root.

    Args:
        project_root (Path): The root directory of the project.

    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    logger.info(f"Initializing Git repository at: {project_root}")
    
    try:
        # Ensure the directory exists
        if not project_root.exists():
            logger.error(f"Project root does not exist: {project_root}")
            return False

        # Run git init
        result = subprocess.run(
            ['git', 'init'],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Git init failed: {result.stderr}")
            return False

        logger.info("Git repository initialized successfully.")
        
        # Configure local user if not set (optional but good for CI)
        # We avoid setting global config, only local if needed for commit
        subprocess.run(['git', 'config', 'user.name', 'llmXive-bot'], cwd=project_root, check=False)
        subprocess.run(['git', 'config', 'user.email', 'bot@llmxive.local'], cwd=project_root, check=False)

        # Create an initial commit to ensure the repo is not empty
        # This is often required for git status to show meaningful history later
        # We create a dummy .gitkeep or rely on existing files if any
        # Since T001 creates structure, we try to add everything
        
        # Check if there are any files to commit
        add_result = subprocess.run(
            ['git', 'add', '.'],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        # Attempt commit only if there are changes or if we force it
        # If the repo is truly empty of tracked files, status might be clean
        # But git init creates the .git folder. 
        # Let's try to commit .gitignore if it exists, or just ensure the repo is valid.
        
        # Verify .git exists
        if (project_root / '.git').is_dir():
            logger.info("Verification: .git directory exists.")
            return True
        else:
            logger.error("Verification failed: .git directory not found.")
            return False

    except FileNotFoundError:
        logger.error("Git command not found. Please ensure Git is installed and in PATH.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during git initialization: {e}")
        return False

def verify_git_repo(project_root: Path) -> dict:
    """
    Verify the git repository status and write the log.

    Args:
        project_root (Path): The root directory of the project.

    Returns:
        dict: Status information including success and log path.
    """
    log_path = project_root / 'data' / 'results' / 'git_status.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Verifying Git repository and writing status to: {log_path}")

    try:
        # Run git status
        result = subprocess.run(
            ['git', 'status'],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        # Write the output to the log file
        with open(log_path, 'w') as f:
            f.write(f"# Git Status Log for PROJ-131\n")
            f.write(f"# Generated at: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}\n")
            f.write(f"# Command: git status\n")
            f.write("-" * 40 + "\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\n# Stderr:\n")
                f.write(result.stderr)

        logger.info(f"Git status log written to {log_path}")
        
        # Return status info
        return {
            "success": True,
            "log_path": str(log_path),
            "has_repo": (project_root / '.git').is_dir()
        }

    except Exception as e:
        logger.error(f"Error verifying git repository: {e}")
        # Write error to log even if it fails
        with open(log_path, 'w') as f:
            f.write(f"# Git Status Verification Failed\n")
            f.write(f"# Error: {e}\n")
        return {
            "success": False,
            "log_path": str(log_path),
            "has_repo": False
        }

def main():
    """
    Main entry point for the Git initialization task.
    """
    # Determine project root (assuming script is in code/ directory)
    # Project root is two levels up from code/setup_git.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    logger.info(f"Starting Git Initialization Task (T002) for project: {project_root}")

    # Step 1: Initialize
    if not initialize_git_repo(project_root):
        logger.error("Failed to initialize Git repository. Aborting.")
        sys.exit(1)

    # Step 2: Verify and Log
    status = verify_git_repo(project_root)

    if status["success"]:
        logger.info("Task T002 completed successfully.")
        print(f"Git repository initialized. Log saved at: {status['log_path']}")
    else:
        logger.error("Task T002 verification failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
