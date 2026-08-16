"""
Script to run Black formatter on the project codebase.
"""
import subprocess
import sys
import os

def main():
    """Run black formatter on the code directory."""
    print("Running Black formatter...")
    try:
        # Run black on the code directory
        result = subprocess.run(
            [sys.executable, "-m", "black", "code/", "tests/"],
            check=True,
            capture_output=False,
            text=True
        )
        if result.returncode == 0:
            print("Formatting complete successfully.")
        else:
            print(f"Formatting exited with code {result.returncode}")
            sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"Error running black: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: black is not installed. Please install it via 'pip install black'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
