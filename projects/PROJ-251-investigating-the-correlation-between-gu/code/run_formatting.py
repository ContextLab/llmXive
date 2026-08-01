import os
import sys
import subprocess
import json
import logging
from pathlib import Path

def run_command(cmd: list, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logging.error(f"Command execution failed: {e}")
        return 1, "", str(e)

def run_ruff_check_and_fix(code_dir: Path) -> Tuple[int, str]:
    """Run ruff check and fix on the code directory."""
    logging.info(f"Running ruff check on {code_dir}")
    
    # First run ruff check to see issues
    returncode, stdout, stderr = run_command(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        cwd=code_dir.parent
    )
    
    if returncode != 0:
        logging.info("Ruff found issues. Attempting to fix...")
        # Run ruff fix
        returncode, stdout, stderr = run_command(
            [sys.executable, "-m", "ruff", "check", "--fix", str(code_dir)],
            cwd=code_dir.parent
        )
        
        if returncode != 0:
            logging.error(f"Ruff check failed after fixes: {stderr}")
            return returncode, f"Ruff check failed: {stderr}"
    
    logging.info("Ruff check passed")
    return 0, "Ruff check passed"

def run_black_format(code_dir: Path) -> Tuple[int, str]:
    """Run black format on the code directory."""
    logging.info(f"Running black format on {code_dir}")
    
    returncode, stdout, stderr = run_command(
        [sys.executable, "-m", "black", str(code_dir)],
        cwd=code_dir.parent
    )
    
    if returncode != 0:
        logging.error(f"Black formatting failed: {stderr}")
        return returncode, f"Black formatting failed: {stderr}"
    
    logging.info("Black formatting completed successfully")
    return 0, "Black formatting completed successfully"

def main():
    """Main entry point for formatting script."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        sys.exit(1)
    
    # Run ruff check and fix
    ruff_code, ruff_msg = run_ruff_check_and_fix(code_dir)
    if ruff_code != 0:
        logger.error(ruff_msg)
        sys.exit(1)
    
    # Run black format
    black_code, black_msg = run_black_format(code_dir)
    if black_code != 0:
        logger.error(black_msg)
        sys.exit(1)
    
    # Generate lint report
    report_path = project_root / "data" / "results" / "lint_report.txt"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, "w") as f:
        f.write(f"Exit code: 0\n")
        f.write(f"Ruff check: PASSED\n")
        f.write(f"Black format: PASSED\n")
        f.write(f"Files processed: {len(list(code_dir.glob('**/*.py')))}\n")
        f.write(f"All formatting issues resolved.\n")
    
    logger.info(f"Lint report written to {report_path}")
    print(f"Formatting completed successfully. Report saved to {report_path}")

if __name__ == "__main__":
    main()
