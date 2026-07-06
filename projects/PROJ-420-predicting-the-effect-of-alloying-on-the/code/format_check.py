"""
Script to enforce Black formatting on all Python files in the code/ directory.

This script acts as a wrapper to ensure consistent formatting across the project
by invoking Black with the project's standard configuration.

Usage:
    python code/format_check.py
    
Exit codes:
    0: All files are correctly formatted
    1: Files need formatting or errors occurred
"""
import subprocess
import sys
from pathlib import Path
from config import get_config
from logging_config import setup_logging, get_logger

def main():
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    config = get_config()
    code_dir = Path(config.code_dir)
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)
    
    logger.info(f"Checking Black formatting in {code_dir}...")
    
    # Find all Python files in code/ directory
    python_files = list(code_dir.glob("**/*.py"))
    
    if not python_files:
        logger.warning("No Python files found in code/ directory.")
        sys.exit(0)
    
    logger.info(f"Found {len(python_files)} Python files to check.")
    
    # Run Black in check mode
    # Using --check to only verify formatting without modifying files
    # Using --diff to show what changes would be made
    cmd = [
        sys.executable, "-m", "black",
        "--check",
        "--diff",
        str(code_dir)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False  # We handle the exit code ourselves
        )
        
        if result.returncode == 0:
            logger.info("All Python files are correctly formatted.")
            sys.exit(0)
        else:
            logger.error("Some files are not formatted correctly. Please run 'black code/' to fix.")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            sys.exit(1)
            
    except FileNotFoundError:
        logger.error("Black is not installed. Please install it via 'pip install black'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running Black: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
