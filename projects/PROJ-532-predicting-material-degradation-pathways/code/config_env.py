"""
Environment Configuration Helper.

This module provides a central way to configure the PYTHONPATH and
other environment variables required for the project to run correctly.
It should be imported early in the execution flow (e.g., at the start
of a script) to ensure all module imports resolve correctly.
"""
import os
import sys
from pathlib import Path

def configure_environment():
    """
    Configures the PYTHONPATH to include the project root directory,
    ensuring that the 'code' package and its submodules are importable.
    
    This function also sets the PYTHONPATH environment variable for
    any subprocesses spawned by this process.
    """
    # Determine the project root (parent of the 'code' directory)
    current_file_path = Path(__file__).resolve()
    code_dir = current_file_path.parent
    project_root = code_dir.parent

    # Add project root to sys.path if not already present
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Update the environment variable for subprocesses
    current_env_path = os.environ.get("PYTHONPATH", "")
    if str(project_root) not in current_env_path:
        if current_env_path:
            os.environ["PYTHONPATH"] = f"{project_root}{os.pathsep}{current_env_path}"
        else:
            os.environ["PYTHONPATH"] = str(project_root)

    return project_root

if __name__ == "__main__":
    # If run directly, print the configuration status
    root = configure_environment()
    print(f"Environment configured. Project root: {root}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    print(f"sys.path (first 3): {sys.path[:3]}")
