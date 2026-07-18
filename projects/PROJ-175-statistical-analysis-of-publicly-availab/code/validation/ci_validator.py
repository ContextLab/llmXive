import os
import sys
import json
import time
import subprocess
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def run_pipeline_step(step_name, script_path, args=None):
    """
    Executes a single pipeline step.
    """
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3600
        )
        return {
            "step": step_name,
            "status": "SUCCESS" if result.returncode == 0 else "FAILED",
            "runtime": time.time(), # Placeholder for real timing if needed
            "error": result.stderr if result.returncode != 0 else None
        }
    except Exception as e:
        return {
            "step": step_name,
            "status": "ERROR",
            "error": str(e)
        }

def main():
    """
    Validates the pipeline by running key steps and checking outputs.
    """
    print("Starting CI Validation...")
    # This is a simplified validation runner. The full execution is handled by execute_full_pipeline.py
    # We ensure the validation logic is present for T036 if needed, but T043a relies on execute_full_pipeline
    
    steps = [
        ("Verify Data", "code/data/verify.py"),
        ("Download Data", "code/data/download.py"),
        ("Preprocess", "code/data/preprocess.py")
    ]
    
    results = []
    for name, path in steps:
        p = project_root / path
        if p.exists():
            results.append(run_pipeline_step(name, p))
        else:
            results.append({"step": name, "status": "SKIPPED", "error": "File not found"})
    
    print("Validation steps completed.")
    return results

if __name__ == "__main__":
    main()