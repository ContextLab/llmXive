"""
Seed‑pinning compliance checker.

Scans the project's Python source files for prohibited direct calls to
``random.seed``, ``np.random.seed`` or ``torch.manual_seed``.  Allowed
usage is via the project's ``code.utils.seeds`` helpers
(``set_seed`` / ``get_seed``).  The script exits with status 0 if no
violations are found, otherwise with status 1 and a summary of the
offending lines.
"""

import argparse
import ast
import sys
from pathlib import Path

# ----------------------------------------------------------------------
# Helper: walk the AST and collect prohibited seed calls
# ----------------------------------------------------------------------
class SeedCallVisitor(ast.NodeVisitor):
    """
    Visits all Call nodes and records those that directly invoke a prohibited
    seeding function without going through ``code.utils.seeds``.
    """
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.violations = []  # List[Tuple[Path, int, str]]

    def visit_Call(self, node: ast.Call):
        # Helper to extract the full dotted name as a string.
        def get_full_name(expr):
            if isinstance(expr, ast.Name):
                return expr.id
            elif isinstance(expr, ast.Attribute):
                value = get_full_name(expr.value)
                return f"{value}.{expr.attr}" if value else expr.attr
            return None

        func_name = get_full_name(node.func)

        # List of prohibited seeding functions (fully qualified).
        prohibited = {
            "random.seed",
            "np.random.seed",
            "numpy.random.seed",
            "torch.manual_seed",
            "torch.cuda.manual_seed",
            "torch.cuda.manual_seed_all",
        }

        if func_name in prohibited:
            # Record the violation with file context.
            self.violations.append((self.file_path, node.lineno, func_name))

        # Continue traversing.
        self.generic_visit(node)

# ----------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------
def find_python_files(root: Path) -> list[Path]:
    """Recursively find all ``.py`` files under *root*."""
    return list(root.rglob("*.py"))

def scan_file(path: Path) -> list[tuple[Path, int, str]]:
    """Parse *path* and return any seed‑pinning violations."""
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        # If the file cannot be read, skip it – CI will catch other issues.
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        # Invalid Python – let the test suite surface this.
        return []
    visitor = SeedCallVisitor(path)
    visitor.visit(tree)
    return visitor.violations

def main():
    parser = argparse.ArgumentParser(
        description="Verify that the project does not use prohibited random seed calls."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Root directory to start scanning (default: current directory)",
    )
    args = parser.parse_args()
    root_path = Path(args.root).resolve()

    all_violations = []

    for py_file in find_python_files(root_path):
        # Skip the compliance script itself to avoid false positives.
        if py_file.samefile(Path(__file__)):
            continue
        all_violations.extend(scan_file(py_file))

    # Exclude any violations that occur inside the official seed‑pinning helper.
    # The helper lives in ``code/utils/seeds.py``; direct calls inside that file
    # are permissible because the module abstracts the seeding logic.
    allowed_modules = {
        root_path / "code" / "utils" / "seeds.py",
    }
    filtered_violations = [
        (path, lineno, func)
        for (path, lineno, func) in all_violations
        if path not in allowed_modules
    ]

    if filtered_violations:
        print("Seed‑pinning violations detected:")
        for path, lineno, func_name in filtered_violations:
            rel_path = path.relative_to(root_path)
            print(f"  {rel_path}:{lineno}: prohibited call to {func_name}")
        sys.exit(1)
    else:
        print("No seed‑pinning violations found.")
        sys.exit(0)

if __name__ == "__main__":
    main()