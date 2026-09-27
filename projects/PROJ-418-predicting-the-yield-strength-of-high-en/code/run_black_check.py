import subprocess
import sys
from pathlib import Path
from utils.logging import get_logger

def run_black_check(target_dir: Path = Path("code")) -> None:
    """
    Run ``black --check`` on the given directory and write the full output
    (stdout and stderr) to ``output/format_report.txt``.

    Parameters
    ----------
    target_dir: Path
        Directory to run the black check on. Defaults to the ``code`` directory.

    Raises
    ------
    RuntimeError
        If black reports any formatting violations (i.e. returns a non‑zero exit code).
    """
    logger = get_logger(__name__)
    logger.info(f"Running black --check on {target_dir}")

    # Use the same interpreter that is executing this script to invoke black as a module.
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(target_dir)],
        capture_output=True,
        text=True,
    )

    # Ensure the output directory exists.
    report_path = Path("output/format_report.txt")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # Write both stdout and stderr to the report for full diagnostics.
    report_path.write_text(result.stdout + "\n" + result.stderr)

    if result.returncode != 0:
        # Black found formatting issues – raise to make the pipeline fail loudly.
        logger.error("Black formatting check failed")
        raise RuntimeError("Code formatting does not comply with Black")
    else:
        logger.info("Black formatting check passed")
        # Black prints a line containing 'All done!' when everything is fine.
        # No further action is required.

def main() -> None:
    """
    Entry‑point used by the task runner. Executes the black check on the
    project's ``code`` directory.
    """
    run_black_check()
