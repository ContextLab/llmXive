"""
Runner script to execute linting and formatting checks.

This module provides a unified entry point to run flake8 and black
checks against the codebase. It can be used in CI/CD pipelines or
locally to verify code quality.
"""

import sys
from pathlib import Path
from code.linting_config import (
    get_black_config,
    get_flake8_config,
    FLAKE8_EXCLUDE,
)

try:
    import black
    import flake8
    from flake8.api import legacy as flake8_api
except ImportError:
    print("Error: linting dependencies not installed.", file=sys.stderr)
    print("Please run: pip install black flake8", file=sys.stderr)
    sys.exit(1)

def run_black_check(target_dir: Path, dry_run: bool = True) -> bool:
    """
    Run black formatting check on the target directory.
    
    Args:
        target_dir: The directory to check.
        dry_run: If True, only check without fixing.
    
    Returns:
        True if all files are correctly formatted, False otherwise.
    """
    config = get_black_config()
    mode = black.Mode(
        line_length=config["line_length"],
        skip_string_normalization=config["skip_string_normalization"],
    )
    
    python_files = []
    for path in target_dir.rglob("*.py"):
        # Skip excluded directories
        is_excluded = any(excluded in path.parts for excluded in FLAKE8_EXCLUDE)
        if not is_excluded:
            python_files.append(str(path))
    
    if not python_files:
        print("No Python files found to check.")
        return True
    
    if dry_run:
        try:
            changed = black.check_files(python_files, mode=mode, quiet=False)
            if changed:
                print("\n❌ Black check failed: Some files need formatting.")
                print("Run: black code/")
                return False
            else:
                print("✅ Black check passed: All files are correctly formatted.")
                return True
        except Exception as e:
            print(f"❌ Black check error: {e}")
            return False
    else:
        try:
            black.format_files(python_files, mode=mode)
            print("✅ Black formatting applied.")
            return True
        except Exception as e:
            print(f"❌ Black formatting error: {e}")
            return False

def run_flake8_check(target_dir: Path) -> bool:
    """
    Run flake8 linting check on the target directory.
    
    Args:
        target_dir: The directory to check.
    
    Returns:
        True if no linting errors found, False otherwise.
    """
    config = get_flake8_config()
    
    # Build exclude pattern string
    exclude_str = ",".join(config["exclude"])
    
    # Create flake8 application
    app = flake8_api.get_application(
        ignore=config["ignore"],
        max_line_length=config["max_line_length"],
        max_complexity=config["max_complexity"],
        exclude=exclude_str,
        show_source=True,
        count=True,
        statistics=True,
    )
    
    try:
        app.run_checks(str(target_dir))
        app.report()
        
        if app.get_file_results():
            error_count = sum(
                len(r.results) for r in app.get_file_results()
            )
            if error_count > 0:
                print(f"\n❌ Flake8 found {error_count} issue(s).")
                return False
        
        print("✅ Flake8 check passed: No linting errors found.")
        return True
    except Exception as e:
        print(f"❌ Flake8 check error: {e}")
        return False

def main():
    """Main entry point for the linting runner."""
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"
    
    print("=" * 60)
    print("Running Code Quality Checks")
    print("=" * 60)
    
    # Run Black check (dry run by default)
    black_ok = run_black_check(code_dir, dry_run=True)
    
    # Run Flake8 check
    flake8_ok = run_flake8_check(code_dir)
    
    print("=" * 60)
    if black_ok and flake8_ok:
        print("🎉 All checks passed!")
        sys.exit(0)
    else:
        print("⚠️ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
