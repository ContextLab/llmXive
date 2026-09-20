import subprocess
import sys
import os
from pathlib import Path
import logging

from config import get_config, setup_logging

def run_command(cmd: list, cwd: Path = None) -> tuple:
    """
    Run a shell command and return (return_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError as e:
        logging.error(f"Command not found: {cmd[0]}")
        return 127, "", str(e)

def main():
    config = get_config()
    logger = setup_logging()
    project_root = Path(config.get("PROJECT_ROOT", "."))
    code_dir = project_root / "code"

    logger.info("Starting linting checks...")
    errors_found = False

    # 1. Black check
    logger.info("Running black --check code/ ...")
    black_cmd = [sys.executable, "-m", "black", "--check", str(code_dir)]
    rc, stdout, stderr = run_command(black_cmd, cwd=project_root)

    if rc == 0:
        logger.info("Black check passed: code is formatted correctly.")
    else:
        errors_found = True
        logger.error("Black check failed:")
        logger.error(stdout)
        if stderr:
            logger.error(stderr)

    # 2. Flake8 check
    logger.info("Running flake8 code/ ...")
    flake8_cmd = [sys.executable, "-m", "flake8", str(code_dir)]
    rc, stdout, stderr = run_command(flake8_cmd, cwd=project_root)

    if rc == 0:
        logger.info("Flake8 check passed: no style/lint errors found.")
    else:
        errors_found = True
        logger.error("Flake8 check failed:")
        logger.error(stdout)
        if stderr:
            logger.error(stderr)

    if errors_found:
        logger.error("Linting checks completed with errors.")
        sys.exit(1)
    else:
        logger.info("All linting checks passed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()