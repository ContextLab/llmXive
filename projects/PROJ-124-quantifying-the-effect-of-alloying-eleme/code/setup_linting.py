"""
Linting and Formatting Setup and Validation Script.

This script configures ruff (linting) and black (formatting) for the project,
generates configuration files, and validates the setup.
"""
import os
import sys
import subprocess
from pathlib import Path
import logging
import json

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

from utils.logger import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)

def check_tool_installed(tool_name: str) -> bool:
    """
    Check if a specific tool (ruff or black) is installed and available.
    
    Args:
        tool_name: Name of the tool to check (e.g., 'ruff', 'black')
        
    Returns:
        True if installed, False otherwise
    """
    try:
        subprocess.run([tool_name, "--version"], check=True, capture_output=True)
        log_info(f"{tool_name} is installed and available.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_warning(f"{tool_name} is not installed or not in PATH.")
        return False

def run_formatting_check(tool_path: Path) -> bool:
    """
    Run black formatting check on the code directory.
    
    Args:
        tool_path: Path to the code directory
        
    Returns:
        True if formatting is correct, False otherwise
    """
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(tool_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log_info("Black formatting check passed.")
            return True
        else:
            log_warning("Black formatting issues detected. Run 'black code/' to fix.")
            # Log first few lines of diff for debugging
            lines = result.stdout.split('\n')
            for line in lines[:10]:
                if line.strip():
                    logger.debug(line)
            return False
    except FileNotFoundError:
        log_error("Black is not installed. Cannot run formatting check.")
        return False
    except Exception as e:
        log_error(f"Error running black check: {e}")
        return False

def run_linting_check(tool_path: Path) -> bool:
    """
    Run ruff linting check on the code directory.
    
    Args:
        tool_path: Path to the code directory
        
    Returns:
        True if linting passes, False otherwise
    """
    try:
        result = subprocess.run(
            ["ruff", "check", str(tool_path)],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log_info("Ruff linting check passed.")
            return True
        else:
            log_warning("Ruff linting issues detected.")
            # Log issues
            if result.stdout:
                logger.warning("Linting issues found:\n%s", result.stdout)
            return False
    except FileNotFoundError:
        log_error("Ruff is not installed. Cannot run linting check.")
        return False
    except Exception as e:
        log_error(f"Error running ruff check: {e}")
        return False

def write_ruff_config(config_path: Path) -> None:
    """
    Write ruff configuration file (ruff.toml).
    
    Args:
        config_path: Path to write the configuration file
    """
    ruff_config = """[lint]
# Select rules
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "S",  # flake8-bandit
]

# Ignore specific rules
ignore = [
    "E501", # Line too long (handled by black)
    "S101", # Use of assert (acceptable in tests)
]

# Allow autofix for all enabled rules (when possible)
fixable = ["ALL"]
unfixable = []

# Exclude files/directories
exclude = [
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    "data/",
    "output/",
    "state/",
    "docs/",
]

# Per-file ignores
[lint.per-file-ignores]
"tests/*" = ["S101"]

[lint.isort]
known-first-party = ["code"]

[format]
# Use Black's formatting settings
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path.write_text(ruff_config)
    log_info(f"Ruff configuration written to {config_path}")

def write_pyproject_config(config_path: Path) -> None:
    """
    Write Black configuration in pyproject.toml.
    
    Args:
        config_path: Path to the pyproject.toml file
    """
    black_config = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.git
  | \.mypy_cache
  | \.ruff_cache
  | data
  | output
  | state
  | docs
)/
'''

[tool.ruff]
# This is handled by ruff.toml, but we can add project metadata here
line-length = 88
target-version = "py311"
"""
    if config_path.exists():
        # Append to existing file
        existing = config_path.read_text()
        if "[tool.black]" not in existing:
            config_path.write_text(existing + "\n" + black_config)
            log_info("Black configuration appended to pyproject.toml")
        else:
            log_info("Black configuration already exists in pyproject.toml")
    else:
        config_path.write_text(black_config)
        log_info(f"pyproject.toml created with Black configuration at {config_path}")

def validate_linting_setup(project_root: Path) -> dict:
    """
    Validate the entire linting and formatting setup.
    
    Args:
        project_root: Root path of the project
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "ruff_installed": False,
        "black_installed": False,
        "ruff_config_exists": False,
        "black_config_exists": False,
        "ruff_check_passed": False,
        "black_check_passed": False,
        "errors": []
    }

    code_path = project_root / "code"

    # Check installations
    results["ruff_installed"] = check_tool_installed("ruff")
    results["black_installed"] = check_tool_installed("black")

    if not results["ruff_installed"] or not results["black_installed"]:
        results["errors"].append("Missing required tools (ruff or black)")
        return results

    # Check configuration files
    ruff_config = project_root / "ruff.toml"
    pyproject_config = project_root / "pyproject.toml"

    results["ruff_config_exists"] = ruff_config.exists()
    results["black_config_exists"] = pyproject_config.exists() and "[tool.black]" in pyproject_config.read_text()

    if not results["ruff_config_exists"]:
        log_warning("ruff.toml not found. Creating default configuration.")
        write_ruff_config(ruff_config)
        results["ruff_config_exists"] = True

    if not results["black_config_exists"]:
        log_warning("Black configuration not found in pyproject.toml. Adding it.")
        write_pyproject_config(pyproject_config)
        results["black_config_exists"] = True

    # Run checks
    if code_path.exists():
        results["ruff_check_passed"] = run_linting_check(code_path)
        results["black_check_passed"] = run_formatting_check(code_path)
    else:
        log_warning("Code directory not found. Skipping lint/format checks.")
        results["errors"].append("Code directory missing")

    return results

def main():
    """
    Main entry point for linting setup and validation.
    """
    project_root = Path(__file__).parent.parent
    log_info("Starting linting and formatting setup validation...")

    results = validate_linting_setup(project_root)

    # Report results
    print("\n" + "="*60)
    print("LINTING AND FORMATTING SETUP REPORT")
    print("="*60)
    
    status = "PASSED"
    if not results["ruff_installed"]:
        print("❌ Ruff is not installed. Please install with: pip install ruff")
        status = "FAILED"
    if not results["black_installed"]:
        print("❌ Black is not installed. Please install with: pip install black")
        status = "FAILED"
    if not results["ruff_config_exists"]:
        print("❌ Ruff configuration missing.")
        status = "FAILED"
    if not results["black_config_exists"]:
        print("❌ Black configuration missing.")
        status = "FAILED"
    if not results["ruff_check_passed"]:
        print("⚠️  Ruff check found issues. Run: ruff check code/")
        status = "WARN"
    if not results["black_check_passed"]:
        print("⚠️  Black check found issues. Run: black code/")
        status = "WARN"

    if status == "PASSED":
        print("✅ All linting and formatting checks passed!")
    elif status == "WARN":
        print("⚠️  Setup is complete, but issues were found.")
        print("   Run 'ruff check code/' and 'black code/' to fix issues.")
    else:
        print("❌ Setup failed. Please install missing tools and configuration.")

    print("="*60)
    print(f"Overall Status: {status}")
    print("="*60 + "\n")

    # Save report
    report_path = project_root / "state" / "linting_setup_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    log_info(f"Report saved to {report_path}")

    # Exit with appropriate code
    if status == "FAILED":
        sys.exit(1)
    elif status == "WARN":
        sys.exit(0) # Warn but don't fail
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()