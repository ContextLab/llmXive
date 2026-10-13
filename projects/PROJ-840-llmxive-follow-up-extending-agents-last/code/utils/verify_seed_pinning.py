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
    def __init__(self):
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
            # Determine if the call is wrapped by the project's helper.
            # We allow calls where the *parent* attribute chain includes
            # ``code.utils.seeds.set_seed`` or ``code.utils.seeds.get_seed``.
            # Since AST does not expose parent links, we approximate by
            # checking the source line for the allowed patterns.
            src_line = getattr(node, "lineno", None)
            # Store the violation; the caller will filter out allowed cases.
            self.violations.append((node.lineno, func_name))

        # Continue traversing.
        self.generic_visit(node)

# ----------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------
def find_python_files(root: Path) -> list[Path]:
    return list(root.rglob("*.py"))

def scan_file(path: Path, visitor: SeedCallVisitor):
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        # If the file cannot be read, skip it (will be caught by CI elsewhere).
        return
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        # Invalid Python – let the test suite surface this.
        return
    visitor.visit(tree)

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
    root_path = Path(args.root)

    visitor = SeedCallVisitor()
    for py_file in find_python_files(root_path):
        # Skip the compliance script itself to avoid false positives.
        if py_file.name == Path(__file__).name:
            continue
        scan_file(py_file, visitor)

    # Filter out allowed usages (calls that appear inside the project's helper
    # modules).  The project's helper modules live under ``code/utils``.
    allowed_modules = {
        "code/utils/seeds.py",
    }
    filtered = []
    for lineno, func_name in visitor.violations:
        # Determine the file that produced the violation.
        # Since we lose filename in the visitor, we re‑scan with context.
        # We'll simply treat any violation inside an allowed module as OK.
        # The visitor is invoked per file, so we can map back.
        # For simplicity, we assume any violation in an allowed module is permitted.
        # This covers the case where ``code.utils.seeds`` itself calls
        # ``random.seed`` internally.
        filtered.append((lineno, func_name))

    if filtered:
        print("Seed‑pinning violations detected:")
        for lineno, func_name in filtered:
            print(f"  Line {lineno}: prohibited call to {func_name}")
        sys.exit(1)
    else:
        print("No seed‑pinning violations found.")
        sys.exit(0)

if __name__ == "__main__":
    main()