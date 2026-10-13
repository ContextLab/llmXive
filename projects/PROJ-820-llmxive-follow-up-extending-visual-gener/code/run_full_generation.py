"""
Convenience wrapper to trigger the full generation phase.
Executes ``code/main.py`` with the ``--phase gen`` shortcut.
"""
import subprocess
import sys
from pathlib import Path

def main():
    # Resolve the path to the main orchestration script
    script_path = Path(__file__).resolve().parent / "main.py"
    if not script_path.is_file():
        print(f"Error: {script_path} not found.", file=sys.stderr)
        sys.exit(1)

    # Run the main script with the required arguments
    cmd = [sys.executable, str(script_path), "--phase", "gen"]
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)

if __name__ == "__main__":
    main()