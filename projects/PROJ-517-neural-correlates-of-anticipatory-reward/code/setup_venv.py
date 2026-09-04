import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Execute the virtual environment setup script.
    
    This script verifies the existence of requirements.txt and then
    executes the setup_venv.sh script to initialize the environment.
    """
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "projects" / "PROJ-517-neural-correlates-of-anticipatory-reward" / "requirements.txt"
    setup_script_path = project_root / "scripts" / "setup_venv.sh"

    # Check if requirements.txt exists
    if not requirements_path.exists():
        print(f"ERROR: requirements.txt not found at {requirements_path}", file=sys.stderr)
        sys.exit(1)

    # Check if setup script exists
    if not setup_script_path.exists():
        print(f"ERROR: setup script not found at {setup_script_path}", file=sys.stderr)
        sys.exit(1)

    # Make script executable if not already
    os.chmod(setup_script_path, 0o755)

    print(f"Executing virtual environment setup from: {setup_script_path}")
    
    try:
        # Execute the shell script
        result = subprocess.run(
            ["bash", str(setup_script_path)],
            cwd=project_root,
            check=True,
            capture_output=False, # Stream output to console
            text=True
        )
        
        if result.returncode == 0:
            print("Virtual environment setup completed successfully.")
        else:
            print(f"Virtual environment setup failed with exit code {result.returncode}", file=sys.stderr)
            sys.exit(result.returncode)
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute setup script: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Shell or script not found: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
