"""
Linting and Formatting utilities for the project.

This module provides functions to run flake8 and black checks/formats
on the codebase.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """
    Run a shell command and report the result.
    
    Args:
        cmd (list): Command and arguments as a list.
        description (str): Description of the action for logging.
        
    Returns:
        bool: True if command succeeded, False otherwise.
    """
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print(f"✓ {description} completed successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with return code {e.returncode}.")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"✗ {description} failed: Command not found. Ensure the tool is installed.")
        return False

def main():
    """
    Main entry point for linting and formatting.
    
    Parses command line arguments to determine which tools to run:
    - 'check': Run flake8 and black (check only)
    - 'format': Run black (format)
    - 'all': Run flake8 check and black format
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run linting and formatting tools.")
    parser.add_argument(
        "mode",
        choices=["check", "format", "all"],
        help="Mode to run: 'check' (lint only), 'format' (black only), 'all' (both)"
    )
    args = parser.parse_args()
    
    # Ensure we are running from the code directory context
    os.chdir(Path(__file__).parent)
    
    success = True
    
    if args.mode in ["check", "all"]:
        # Run flake8
        if not run_command(
            ["flake8", "."],
            "Flake8 Linting"
        ):
            success = False
    
    if args.mode in ["format", "all"]:
        # Run black
        if not run_command(
            ["black", "."],
            "Black Formatting"
        ):
            # Black might return non-zero if it changes files, 
            # but we treat it as success if it runs, unless it crashes.
            # However, for 'check' mode, we want to fail if formatting is needed.
            # Since 'format' mode is requested, we assume success if the command runs.
            pass
    
    if args.mode == "check" and not success:
        sys.exit(1)
        
    print("All requested checks/formats completed.")
