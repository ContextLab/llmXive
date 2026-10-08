"""
Linting and formatting configuration and execution utilities.
Provides functions to run flake8, black, and isort on the project codebase.
"""
import os
import subprocess
import sys
from pathlib import Path
from logger import get_logger, error, info

logger = get_logger(__name__)

def ensure_config_files():
    """
    Ensure flake8 and black configuration files exist in the project root.
    Creates them if they are missing.
    """
    root = Path(__file__).parent.parent
    flake8_cfg = root / ".flake8"
    black_cfg = root / "pyproject.toml"

    if not flake8_cfg.exists():
        content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    .eggs,
    *.egg-info
"""
        flake8_cfg.write_text(content)
        info(f"Created {flake8_cfg}")

    if not black_cfg.exists():
        # Check if pyproject.toml exists but lacks [tool.black]
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text()
            if "[tool.black]" not in text:
                with open(pyproject, "a") as f:
                    f.write("\n[tool.black]\nline-length = 88\n")
                info("Added [tool.black] section to pyproject.toml")
        else:
            content = """[tool.black]
line-length = 88
target-version = ['py38']
"""
            pyproject.write_text(content)
            info(f"Created {pyproject} with black config")
    else:
        # Verify pyproject.toml has black config if it exists
        text = black_cfg.read_text()
        if "[tool.black]" not in text:
            with open(black_cfg, "a") as f:
                f.write("\n[tool.black]\nline-length = 88\n")
            info("Added [tool.black] section to existing pyproject.toml")

def run_flake8(target_dir: str = "code") -> bool:
    """
    Run flake8 on the specified directory.
    Returns True if no errors found, False otherwise.
    """
    logger.info(f"Running flake8 on {target_dir}/")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", target_dir],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        
        if result.returncode == 0:
            info("flake8: No issues found.")
            return True
        else:
            error(f"flake8 found {result.returncode} issues.")
            return False
    except Exception as e:
        error(f"Failed to run flake8: {e}")
        return False

def run_black(target_dir: str = "code", check_only: bool = False) -> bool:
    """
    Run black on the specified directory.
    If check_only is True, only check formatting without modifying files.
    Returns True if formatting is correct (or fixed), False if check_only fails.
    """
    logger.info(f"Running black on {target_dir}/")
    try:
        cmd = [sys.executable, "-m", "black"]
        if check_only:
            cmd.append("--check")
            cmd.append("--diff")
        cmd.append(target_dir)
        
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            # If check_only, stdout contains the diff
            if check_only:
                if result.returncode == 0:
                    info("black: All files are formatted correctly.")
                    return True
                else:
                    logger.warning("black: Formatting issues found. Run without --check to fix.")
                    # Log a summary of the diff if too long
                    lines = result.stdout.split('\n')
                    for line in lines[:20]:
                        logger.warning(line)
                    if len(lines) > 20:
                        logger.warning(f"... and {len(lines) - 20} more lines")
                    return False
            else:
                logger.info(result.stdout)
        
        if result.stderr:
            logger.warning(result.stderr)
        
        if result.returncode == 0:
            info("black: Formatting applied successfully.")
            return True
        else:
            error("black: Failed to format files.")
            return False
    except Exception as e:
        error(f"Failed to run black: {e}")
        return False

def run_isort(target_dir: str = "code") -> bool:
    """
    Run isort on the specified directory to sort imports.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Running isort on {target_dir}/")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", target_dir],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        
        if result.returncode == 0:
            info("isort: Imports sorted successfully.")
            return True
        else:
            error("isort: Failed to sort imports.")
            return False
    except Exception as e:
        error(f"Failed to run isort: {e}")
        return False

def main():
    """
    Main entry point to run all linting and formatting tools.
    Ensures config files exist, then runs isort, black, and flake8.
    """
    root = Path(__file__).parent.parent
    logger.info("Starting linting and formatting workflow...")
    
    ensure_config_files()
    
    # Run isort first to sort imports
    if not run_isort("code"):
        logger.warning("isort encountered issues.")
    
    # Run black to format code
    if not run_black("code"):
        logger.warning("black encountered issues. Re-running check...")
        run_black("code", check_only=True)
    
    # Run flake8 to check for linting errors
    flake8_ok = run_flake8("code")
    
    if flake8_ok:
        logger.info("Linting and formatting workflow completed successfully.")
    else:
        logger.error("Linting workflow completed with errors. Please fix reported issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()