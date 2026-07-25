import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, Optional

def run_command(command: list[str], cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """
    Execute a shell command and return (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main() -> None:
    """
    Main entry point to run ruff check and black format on the code/ directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        print(f"Error: Code directory not found at {code_dir}")
        sys.exit(1)

    logger = logging.getLogger("formatter")
    logger.info(f"Running formatting tools on {code_dir}")

    # Run ruff check
    print("Running ruff check...")
    ruff_check_cmd = [sys.executable, "-m", "ruff", "check", str(code_dir)]
    returncode, stdout, stderr = run_command(ruff_check_cmd, cwd=project_root)
    print(stdout)
    if stderr:
        print(f"Stderr: {stderr}")
    
    if returncode != 0:
        print("Ruff check found issues. Attempting auto-fix...")
        # Run ruff check with --fix
        ruff_fix_cmd = [sys.executable, "-m", "ruff", "check", "--fix", str(code_dir)]
        returncode, stdout, stderr = run_command(ruff_fix_cmd, cwd=project_root)
        print(stdout)
        if stderr:
            print(f"Stderr: {stderr}")

    # Run black format
    print("Running black format...")
    black_cmd = [sys.executable, "-m", "black", str(code_dir)]
    returncode, stdout, stderr = run_command(black_cmd, cwd=project_root)
    print(stdout)
    if stderr:
        print(f"Stderr: {stderr}")

    print("Formatting complete.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    main()
