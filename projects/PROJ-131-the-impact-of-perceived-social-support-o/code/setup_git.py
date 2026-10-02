"""
Setup Git Repository for the project.
Initializes a git repository and logs the status.
"""
import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repo(root_dir: Path) -> bool:
    """
    Initialize a git repository in the specified directory.
    
    Args:
        root_dir: The root directory to initialize git in.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Change to the root directory
        os.chdir(root_dir)
        
        # Check if git is already initialized
        result = subprocess.run(
            ['git', 'rev-parse', '--is-inside-work-tree'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Git repository already exists in {root_dir}")
            return True
        
        # Initialize git repository
        print(f"Initializing git repository in {root_dir}")
        init_result = subprocess.run(
            ['git', 'init'],
            capture_output=True,
            text=True
        )
        
        if init_result.returncode != 0:
            print(f"Error initializing git repository: {init_result.stderr}")
            return False
        
        print("Git repository initialized successfully")
        return True
        
    except Exception as e:
        print(f"Exception during git initialization: {str(e)}")
        return False

def verify_git_repo(root_dir: Path) -> bool:
    """
    Verify that a git repository exists in the specified directory.
    
    Args:
        root_dir: The root directory to check.
        
    Returns:
        True if git repository exists, False otherwise.
    """
    try:
        os.chdir(root_dir)
        result = subprocess.run(
            ['git', 'status'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Git repository verified successfully")
            return True
        else:
            print(f"Git repository verification failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Exception during git verification: {str(e)}")
        return False

def main():
    """
    Main function to initialize and verify git repository.
    Creates a log file with the git status.
    """
    # Determine project root (assume script is in code/ directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Project root: {project_root}")
    
    # Initialize git repository
    if not initialize_git_repo(project_root):
        print("Failed to initialize git repository")
        sys.exit(1)
    
    # Verify git repository
    if not verify_git_repo(project_root):
        print("Failed to verify git repository")
        sys.exit(1)
    
    # Create log directory if it doesn't exist
    results_dir = project_root / 'data' / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Get git status and write to log file
    try:
        os.chdir(project_root)
        status_result = subprocess.run(
            ['git', 'status'],
            capture_output=True,
            text=True
        )
        
        log_file = results_dir / 'git_status.log'
        with open(log_file, 'w') as f:
            f.write(status_result.stdout)
            if status_result.stderr:
                f.write(f"STDERR:\n{status_result.stderr}")
        
        print(f"Git status logged to {log_file}")
        
    except Exception as e:
        print(f"Error writing git status log: {str(e)}")
        sys.exit(1)
    
    print("Git repository setup completed successfully")

if __name__ == "__main__":
    main()
