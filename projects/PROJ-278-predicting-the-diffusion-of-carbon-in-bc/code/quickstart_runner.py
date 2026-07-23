import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def run_script(script_name: str, args: list = None) -> subprocess.CompletedProcess:
    """
    Execute a Python script from the code directory.
    
    Args:
        script_name: Name of the script in code/ (e.g., '01_download.py')
        args: Optional list of command line arguments
        
    Returns:
        CompletedProcess instance
        
    Raises:
        RuntimeError: If the script returns a non-zero exit code
    """
    script_path = PROJECT_ROOT / "code" / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    
    if result.returncode != 0:
        error_msg = (
            f"Script {script_name} failed.\n"
            f"Return code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
        raise RuntimeError(error_msg)
    
    return result

def main():
    """
    Main entry point for running the quickstart pipeline.
    Executes 01_download, 02_preprocess, 03_train, and 04_evaluate in sequence.
    """
    scripts = [
        "01_download.py",
        "02_preprocess.py",
        "03_train.py",
        "04_evaluate.py"
    ]
    
    print("Starting Quickstart Pipeline Validation (T024)...")
    
    try:
        for script in scripts:
            print(f"\n--- Running {script} ---")
            run_script(script)
            print(f"✓ {script} completed successfully")
        
        print("\n" + "="*50)
        print("Quickstart Pipeline Validation: SUCCESS")
        print("="*50)
        
    except RuntimeError as e:
        print("\n" + "="*50)
        print("Quickstart Pipeline Validation: FAILED")
        print("="*50)
        print(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
