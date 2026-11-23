import subprocess
import sys
import os
import logging
from pathlib import Path

def run_command(cmd: list, cwd: Path) -> tuple:
    """
    Run a shell command and return (success, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return (result.returncode == 0, result.stdout, result.stderr)
    except Exception as e:
        logging.error(f"Command failed to execute: {e}")
        return (False, "", str(e))

def create_dummy_init_if_needed(init_path: Path) -> bool:
    """
    Ensure code/__init__.py exists. Create it if missing.
    """
    if not init_path.exists():
        logging.info(f"Creating missing {init_path}")
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.write_text("# Project root package\n")
        return True
    return False

def append_to_checksums_file(checksum_path: Path, command_name: str, success: bool, output: str):
    """
    Append the result of a linting check to data/checksums.txt.
    Format: # <command>: <status>
    """
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, 'a') as f:
        status = "PASSED" if success else "FAILED"
        f.write(f"# {command_name}: {status}\n")
        if output:
            f.write(output + "\n")
        f.write("\n")

def main():
    """
    Verify linting configuration by running black and flake8 on code/.
    Appends results to data/checksums.txt.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    checksums_file = project_root / "data" / "checksums.txt"

    # Ensure __init__.py exists (Task requirement)
    init_file = code_dir / "__init__.py"
    create_dummy_init_if_needed(init_file)

    # 1. Run black --check
    logger.info("Running black --check...")
    black_cmd = [sys.executable, "-m", "black", "--check", str(code_dir)]
    black_success, black_out, black_err = run_command(black_cmd, project_root)

    if black_success:
        logger.info("Black check passed.")
    else:
        logger.warning("Black check failed. Outputting errors to checksums.txt.")
        # Note: In a strict CI, this might exit 1, but per task we log and continue

    # 2. Run flake8
    logger.info("Running flake8...")
    flake8_cmd = [sys.executable, "-m", "flake8", str(code_dir)]
    flake8_success, flake8_out, flake8_err = run_command(flake8_cmd, project_root)

    if flake8_success:
        logger.info("Flake8 check passed.")
    else:
        logger.warning("Flake8 check failed. Outputting errors to checksums.txt.")

    # 3. Append results to checksums.txt
    append_to_checksums_file(
        checksums_file,
        "black",
        black_success,
        black_err if not black_success else black_out
    )
    append_to_checksums_file(
        checksums_file,
        "flake8",
        flake8_success,
        flake8_err if not flake8_success else flake8_out
    )

    logger.info("Linting verification complete. Results appended to data/checksums.txt")

    # Return exit code based on combined success
    if black_success and flake8_success:
        sys.exit(0)
    else:
        # Task says "Verify... Redirect output", implies we log the failure but
        # the script itself documents the state. If strict pass is required,
        # we might exit 1. Given the task is "Verify", we report the state.
        # However, standard practice for "check" is to fail if errors found.
        sys.exit(1)

if __name__ == "__main__":
    main()