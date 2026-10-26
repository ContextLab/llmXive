"""
Verification script that scans all Python modules under the ``code/`` directory
and ensures each imports the project‑wide logger via
``from utils.logging_config import get_logger`` (or via the legacy
``utils.logger`` wrapper).

It also checks that a ``logger`` variable is defined at module level.
The script writes a short summary to the pipeline log and exits with
status 0 if all modules pass, otherwise with status 1.
"""

import sys
import ast
from pathlib import Path

from utils.logging_config import get_logger

logger = get_logger(__name__)

def _module_uses_logger(tree: ast.Module) -> bool:
    """
    Return True if the AST defines a name ``logger`` at module scope.
    """
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "logger":
                    return True
    return False

def _module_imports_get_logger(tree: ast.Module) -> bool:
    """
    Return True if the AST contains an import of ``get_logger`` from
    ``utils.logging_config`` (or from ``utils.logger``).
    """
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module in ("utils.logging_config", "utils.logger"):
                for alias in node.names:
                    if alias.name == "get_logger":
                        return True
    return False

def verify_codebase(root: Path) -> bool:
    """
    Walk the ``code/`` directory and verify each ``.py`` file imports
    and defines a ``logger`` variable.
    """
    all_ok = True
    for py_path in root.rglob("*.py"):
        # Skip the verification script itself and the logger implementation
        if py_path.name in ("verify_logging_imports.py", "logger.py"):
            continue

        try:
            source = py_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_path))
        except Exception as e:
            logger.error(f"Failed to parse {py_path}: {e}")
            all_ok = False
            continue

        imports_logger = _module_imports_get_logger(tree)
        defines_logger = _module_uses_logger(tree)

        if not imports_logger:
            logger.error(f"{py_path} does NOT import get_logger.")
            all_ok = False
        if not defines_logger:
            logger.error(f"{py_path} does NOT define a module‑level ``logger`` variable.")
            all_ok = False

    if all_ok:
        logger.info("All modules correctly import and expose a ``logger``.")
    else:
        logger.error("Some modules are missing logger imports or definitions.")
    return all_ok

def main():
    project_root = Path(__file__).resolve().parents[2]  # <project>/code/
    code_root = project_root / "code"
    success = verify_codebase(code_root)
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
