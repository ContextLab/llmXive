import os
import sys
import subprocess
from pathlib import Path

def run_script(script_path: str):
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Script {script_path} failed: {result.stderr}")
    return result.stdout

def main():
    scripts = [
        "code/01_download.py",
        "code/02_preprocess.py",
        "code/03_train.py",
        "code/04_evaluate.py",
        "code/05_validate.py"
    ]
    for script in scripts:
        print(f"Running {script}...")
        run_script(script)
        print(f"Completed {script}")
