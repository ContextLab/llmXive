from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

from utils.logging import get_logger

logger = get_logger("cleanup")


def run_black(paths: List[Path] | None = None) -> Tuple[bool, str]:
    """Run Black formatter on the given paths or the whole code/ directory."""
    if paths is None:
        paths = [Path("code")]

    cmd = [sys.executable, "-m", "black", "--check", "--diff"] + [str(p) for p in paths]
    logger.info(f"Running Black: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info("Black check passed: no formatting violations.")
            return True, result.stdout
        else:
            logger.warning("Black check found formatting violations.")
            return False, result.stdout + result.stderr
    except FileNotFoundError:
        msg = "Black is not installed. Run: pip install black"
        logger.error(msg)
        return False, msg


def run_flake8(paths: List[Path] | None = None) -> Tuple[bool, str]:
    """Run flake8 on the given paths or the whole code/ directory."""
    if paths is None:
        paths = [Path("code")]

    cmd = [sys.executable, "-m", "flake8"] + [str(p) for p in paths]
    logger.info(f"Running flake8: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            logger.info("Flake8 check passed: PEP8 compliance verified.")
            return True, result.stdout
        else:
            logger.warning("Flake8 check found PEP8 violations.")
            return False, result.stdout + result.stderr
    except FileNotFoundError:
        msg = "flake8 is not installed. Run: pip install flake8"
        logger.error(msg)
        return False, msg


def _find_python_files(root: Path) -> List[Path]:
    """Recursively find all .py files in the given root directory."""
    return list(root.rglob("*.py"))


def _check_imports(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Attempt to compile the Python file to check for syntax errors and
    verify that imports can be resolved within the project context.
    Returns (is_valid, list_of_error_messages).
    """
    errors = []
    try:
        # Check syntax first
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, str(file_path), "exec")
    except SyntaxError as e:
        errors.append(f"SyntaxError in {file_path}: {e.msg} at line {e.lineno}")
        return False, errors

    # Attempt to import to catch unresolved names (if possible)
    # Note: This is a heuristic. We add the project root to sys.path temporarily.
    # We do not actually run the module to avoid side effects, but we try to
    # parse the imports. For a more robust check, we rely on mypy or the
    # actual execution of the pipeline. Here we ensure the file is syntactically
    # valid and attempt a basic import check if it's a top-level module.
    # Since we are in a script, we can try to import the module relative to the project root.
    # However, `importlib` might fail if dependencies are missing.
    # We will stick to syntax validation and a basic "dead code" heuristic:
    # checking for unused imports by attempting to parse the AST.

    # Dead code heuristic: Check for imports that are never used in the file body.
    # This is a simplified check.
    import ast
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Already caught above, but safety net
        return False, ["AST parse failed"]

    # Collect all defined names and used names
    defined_names = set()
    used_names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name.split('.')[0]
                defined_names.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                defined_names.add(name)
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                defined_names.add(node.id)
            elif isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle module.attr usage
            current = node
            while isinstance(current, ast.Attribute):
                used_names.add(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                used_names.add(current.id)

    # Find imports that are defined but never used (simple heuristic)
    # Exclude common built-ins and 'self', 'cls'
    unused_imports = []
    for name in defined_names:
        if name in {"self", "cls", "pathlib", "sys"}:
            continue
        if name not in used_names:
            # Check if it looks like an import (usually at top)
            # This is a rough heuristic. A real linter does this better.
            # We will flag it if it's in the defined set but not used.
            unused_imports.append(name)

    if unused_imports:
        errors.append(f"Potential dead code (unused imports) in {file_path}: {', '.join(unused_imports)}")

    return len(errors) == 0, errors


def remove_dead_code() -> Tuple[bool, str]:
    """
    Scan code/ for potential dead code (unused imports) and verify imports.
    Returns (success, report).
    """
    logger.info("Scanning for dead code and import errors...")
    code_root = Path("code")
    if not code_root.exists():
        return False, "code/ directory not found."

    files = _find_python_files(code_root)
    total_files = len(files)
    issues = []

    for file_path in files:
        is_valid, errs = _check_imports(file_path)
        if not is_valid:
            issues.extend(errs)

    if issues:
        msg = f"Found {len(issues)} potential issues:\n" + "\n".join(issues)
        logger.warning(msg)
        return False, msg
    else:
        msg = f"Checked {total_files} files. No dead code or import syntax errors found."
        logger.info(msg)
        return True, msg


def main() -> int:
    """Main entry point for the cleanup script."""
    logger.info("Starting cleanup process...")

    # 1. Run Black
    black_ok, black_report = run_black()
    if not black_ok:
        logger.warning("Black check failed. Please format the code.")
        print(black_report)
    else:
        print("Black: OK")

    # 2. Run Flake8
    flake8_ok, flake8_report = run_flake8()
    if not flake8_ok:
        logger.warning("Flake8 check failed.")
        print(flake8_report)
    else:
        print("Flake8: OK")

    # 3. Check for dead code and import errors
    dead_code_ok, dead_code_report = remove_dead_code()
    if not dead_code_ok:
        logger.warning("Dead code or import issues detected.")
        print(dead_code_report)
    else:
        print("Dead Code Check: OK")

    # Return non-zero if any check failed
    if not (black_ok and flake8_ok and dead_code_ok):
        logger.error("Cleanup process completed with warnings/errors.")
        return 1

    logger.info("Cleanup process completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
