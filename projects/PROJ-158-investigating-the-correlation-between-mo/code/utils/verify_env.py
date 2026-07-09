import subprocess
import sys
import os

def main():
    """
    Verifies that the dependencies in code/requirements.txt can be installed
    (dry-run) and checks Python version.
    """
    req_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt")
    
    if not os.path.exists(req_path):
        print(f"Error: requirements.txt not found at {req_path}")
        sys.exit(1)

    # Check Python version
    if sys.version_info < (3, 11):
        print(f"Warning: Python version {sys.version_info.major}.{sys.version_info.minor} detected. "
              f"Task requires Python 3.11 or higher.")
        # We do not exit here as the environment might be managed externally,
        # but we log the warning.

    print(f"Checking Python version: {sys.version}")
    print(f"Checking dry-run installation for: {req_path}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path, "--dry-run"],
            check=True,
            capture_output=True,
            text=True
        )
        print("Dry-run successful. Dependencies are valid.")
        # Print a snippet of the output to confirm
        if result.stdout:
            # Filter out verbose pip output, just show summary if available
            lines = result.stdout.split('\n')
            for line in lines:
                if 'would install' in line or 'already satisfied' in line:
                    print(line)
            if not any('would install' in l or 'already satisfied' in l for l in lines):
                print("Installation check passed (no specific summary line found, but exit code 0).")
    except subprocess.CalledProcessError as e:
        print(f"Error: Dry-run failed. pip returned exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()