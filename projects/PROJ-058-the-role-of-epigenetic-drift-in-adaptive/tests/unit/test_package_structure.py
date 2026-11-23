"""
Tests for T005: package structure via ``__init__.py`` files.

Verifies that:
1. ``code/__init__.py`` exists, is valid Python, and can be loaded
   without side effects.
2. Every code subpackage (discovery, preprocess, analysis, viz) has an
   ``__init__.py``.
3. ``code/analysis/__init__.py`` no longer uses the broken unqualified
   ``from correlation import ...`` style that caused
   ``ModuleNotFoundError`` in the pipeline entry point.
"""

import ast
import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"


def test_code_init_exists_and_compiles():
    init_file = CODE_DIR / "__init__.py"
    assert init_file.is_file(), f"Missing {init_file}"
    source = init_file.read_text(encoding="utf-8")
    ast.parse(source)  # raises SyntaxError if invalid


def test_code_init_loads_without_side_effects():
    init_file = CODE_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        "epigenetic_drift_code_init", init_file
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.__version__ == "0.1.0"


def test_subpackage_init_files_exist():
    for sub in ("discovery", "preprocess", "analysis", "viz"):
        init_file = CODE_DIR / sub / "__init__.py"
        assert init_file.is_file(), f"Missing {init_file}"
        ast.parse(init_file.read_text(encoding="utf-8"))


def test_analysis_init_uses_relative_imports():
    """
    The execution failure showed ``from correlation import ...`` raising
    ModuleNotFoundError. The fixed file must use package-relative imports
    (``from .correlation import ...``) for sibling modules.
    """
    init_file = CODE_DIR / "analysis" / "__init__.py"
    source = init_file.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module in (
                "correlation",
                "timescale_align",
                "sensitivity",
                "stability_check",
                "stressor_stratification",
            ):
                raise AssertionError(
                    f"Unqualified import 'from {node.module} import ...' "
                    "found in code/analysis/__init__.py; use relative "
                    "imports (from .module import ...) instead."
                )
    # And at least one relative import must be present
    relative_imports = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.level > 0
    ]
    assert relative_imports, "No relative imports found in analysis/__init__.py"