import subprocess
import sys
import os

def run_command(command):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr

def main():
    """Run ruff linting on the project."""
    print("Running ruff lint...")
    returncode, stdout, stderr = run_command("ruff check code/")

    if stdout:
        print(stdout)
    if stderr:
        print(stderr)

    if returncode != 0:
        print("Linting failed.")
        sys.exit(1)
    else:
        print("Linting passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
