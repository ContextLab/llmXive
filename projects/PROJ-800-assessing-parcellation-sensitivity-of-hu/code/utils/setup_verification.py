"""
Verification script for T002: Verify directory creation.
Executes `ls -R` on the project root and captures output to state/setup_verification.log.
"""
import os
import subprocess
import sys
from pathlib import Path

# Add project root to path to ensure imports work if needed,
# though this script is self-contained.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_DIR = PROJECT_ROOT / "projects" / "PROJ-800-assessing-parcellation-sensitivity-of-hu"
STATE_DIR = PROJECT_ROOT / "state"
LOG_FILE = STATE_DIR / "setup_verification.log"

def main():
    """Verify directory creation and log output."""
    if not PROJECT_DIR.exists():
        error_msg = f"Error: Project directory does not exist: {PROJECT_DIR}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    # Ensure state directory exists to write the log
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Execute ls -R on the project directory
        # Using subprocess.run with capture_output=True to get the result
        result = subprocess.run(
            ["ls", "-R", str(PROJECT_DIR)],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout

        # Write output to log file
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(output)

        print(f"Verification successful. Output written to: {LOG_FILE}")
        print("Directory structure confirmed:")
        print(output)

    except subprocess.CalledProcessError as e:
        error_msg = f"Error executing 'ls -R': {e.stderr}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        # This shouldn't happen if PROJECT_DIR exists, but good to handle
        error_msg = f"Error: Directory not found during verification: {PROJECT_DIR}"
        print(error_msg, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
