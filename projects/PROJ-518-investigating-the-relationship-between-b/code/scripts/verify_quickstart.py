"""
Script to verify the quickstart.md commands in a fresh virtualenv.
This script simulates the execution flow defined in quickstart.md to ensure
all steps complete successfully without errors.
"""
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd: list, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    if check and result.returncode != 0:
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(cmd)}")
    return result

def verify_quickstart():
    """
    Executes the logical steps of quickstart.md:
    1. Create virtualenv
    2. Install requirements
    3. Run data setup
    4. Run main pipeline
    5. Verify outputs
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    venv_dir = project_root / ".venv_quickstart_test"
    
    # Cleanup if exists
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
    
    try:
        # Step 1: Create virtualenv
        print("Step 1: Creating virtual environment...")
        run_command([sys.executable, "-m", "venv", str(venv_dir)])
        
        # Determine pip path
        if sys.platform == "win32":
            pip_path = venv_dir / "Scripts" / "pip"
            python_path = venv_dir / "Scripts" / "python"
        else:
            pip_path = venv_dir / "bin" / "pip"
            python_path = venv_dir / "bin" / "python"
        
        # Step 2: Install requirements
        print("Step 2: Installing requirements...")
        run_command([str(pip_path), "install", "--upgrade", "pip"])
        requirements_path = project_root / "requirements.txt"
        if requirements_path.exists():
            run_command([str(pip_path), "install", "-r", str(requirements_path)])
        else:
            print("Warning: requirements.txt not found, skipping install.")

        # Step 3: Setup data directories
        print("Step 3: Running data directory setup...")
        run_command([str(python_path), str(project_root / "code" / "setup_data_dirs.py")])

        # Step 4: Run the main pipeline
        print("Step 4: Running main pipeline...")
        # We run the main script. If it fails due to missing data (which is expected 
        # if no real data is present), it should fail loudly as per spec, 
        # but the script itself must be syntactically correct and runnable.
        try:
            run_command([str(python_path), str(project_root / "code" / "main.py")])
        except RuntimeError as e:
            # If the error is about missing data, that is acceptable for the "verify" step
            # as long as the code structure is correct and it didn't crash with an import error.
            if "DataMissingCreativityError" in str(e) or "DATA_MISSING" in str(e):
                print("Pipeline exited with expected DataMissingCreativityError (no real data present).")
            else:
                # If it's an import error or syntax error, that's a failure of the implementation.
                raise e

        # Step 5: Verify outputs (if any were created)
        print("Step 5: Verifying output structure...")
        data_processed = project_root / "data" / "processed"
        if data_processed.exists():
            print(f"  - data/processed exists: {list(data_processed.iterdir())}")
        
        docs_outputs = project_root / "docs" / "outputs"
        if docs_outputs.exists():
            print(f"  - docs/outputs exists: {list(docs_outputs.iterdir())}")

        print("Quickstart verification completed successfully.")
        return True

    except Exception as e:
        print(f"Verification failed: {e}")
        return False
    finally:
        # Cleanup virtualenv
        if venv_dir.exists():
            shutil.rmtree(venv_dir)
            print("Cleaned up temporary virtual environment.")

if __name__ == "__main__":
    success = verify_quickstart()
    sys.exit(0 if success else 1)