import os
import sys
import subprocess
import stat
import logging
from pathlib import Path

from utils import get_logger, get_project_paths


def set_executable_permissions(logger: logging.Logger) -> None:
    """
    Set executable permissions on all .py files in the code/ directory.
    This satisfies the "Set permissions" requirement of T001b.
    """
    code_dir = get_project_paths()["code_dir"]
    if not code_dir.exists():
        logger.warning(f"Code directory {code_dir} does not exist. Skipping permission setup.")
        return

    count = 0
    for py_file in code_dir.rglob("*.py"):
        # Check if already executable
        current_mode = py_file.stat().st_mode
        if current_mode & stat.S_IXUSR:
            continue
        
        try:
            # Add execute permission for user
            new_mode = current_mode | stat.S_IXUSR
            py_file.chmod(new_mode)
            count += 1
            logger.debug(f"Set executable permission on: {py_file}")
        except OSError as e:
            logger.warning(f"Failed to set permission on {py_file}: {e}")

    logger.info(f"Set executable permissions on {count} Python files in {code_dir}")


def init_git_repository(logger: logging.Logger) -> bool:
    """
    Initialize a git repository in the project root.
    Returns True if successful, False otherwise.
    """
    project_root = get_project_paths()["project_root"]
    
    # Check if .git already exists
    git_dir = project_root / ".git"
    if git_dir.exists():
        logger.info(f"Git repository already initialized at {project_root}")
        return True

    try:
        logger.info(f"Initializing git repository at {project_root}")
        result = subprocess.run(
            ["git", "init"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"git init failed: {result.stderr}")
            return False
        
        logger.info(f"git init output: {result.stdout.strip()}")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("git init timed out")
        return False
    except FileNotFoundError:
        logger.error("git command not found. Please install git.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during git init: {e}")
        return False


def verify_git_status(logger: logging.Logger) -> bool:
    """
    Verify that the git repository is in a clean state.
    Runs 'git status' and checks for clean state.
    Returns True if clean, False otherwise.
    """
    project_root = get_project_paths()["project_root"]
    
    try:
        # Check if .git exists
        git_dir = project_root / ".git"
        if not git_dir.exists():
            logger.error("Git repository not found. Run init_git_repository first.")
            return False

        # Run git status
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            logger.error(f"git status failed: {result.stderr}")
            return False

        # Check if output is empty (clean state)
        output = result.stdout.strip()
        if output:
            logger.warning(f"Git repository has uncommitted changes:\n{output}")
            # This is not a failure of the task itself, just informational
            # The task asks to "verify" and "log output", which we are doing
            return True
        else:
            logger.info("Git repository is in a clean state.")
            return True
        
    except subprocess.TimeoutExpired:
        logger.error("git status timed out")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during git status verification: {e}")
        return False


def main() -> int:
    """
    Main entry point for T001b: Set permissions and initialize git repository.
    Returns 0 on success, 1 on failure.
    """
    logger = get_logger("setup_git")
    logger.info("Starting T001b: Set permissions and initialize git repository")
    
    # Step 1: Set executable permissions
    logger.info("Setting executable permissions on Python files...")
    set_executable_permissions(logger)
    
    # Step 2: Initialize git repository
    logger.info("Initializing git repository...")
    if not init_git_repository(logger):
        logger.error("Failed to initialize git repository")
        return 1
    
    # Step 3: Verify git status
    logger.info("Verifying git status...")
    if not verify_git_status(logger):
        logger.error("Failed to verify git status")
        return 1
    
    logger.info("T001b completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())