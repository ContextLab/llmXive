"""
Seed Pinning Compliance Verifier (Task T004b).

This script scans all Python files in the `code/` directory to ensure that
every random operation (e.g., `random.seed`, `np.random.seed`, `torch.manual_seed`)
uses `seeds.get_seed(task_id)` (or the wrapper `seeds.set_seed`) as mandated by FR-008.

It exits with code 0 if compliant, 1 if any violation is found.
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Set

# Directory containing the project's source code
CODE_ROOT = Path("code")

# Functions that are allowed (they come from the project's seed utility)
ALLOWED_SEED_FUNCTIONS = {
    "seeds.set_seed",
    "seeds.get_seed",
    "seeds.restore_seed_state",
    "seeds.verify_seed",
}

# Direct calls that are prohibited unless they go through the seed utility
FORBIDDEN_DIRECT_CALLS = {
    "random.seed",
    "np.random.seed",
    "numpy.random.seed",
    "torch.manual_seed",
    "torch.cuda.manual_seed",
    "torch.cuda.manual_seed_all",
    "torch.backends.cudnn.deterministic",
}

class SeedComplianceVisitor(ast.NodeVisitor):
    """AST visitor that records prohibited seed calls."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.violations: List[Tuple[int, str]] = []
        # Mapping from alias name to fully‑qualified module name (e.g. {"np": "numpy"})
        self.aliases: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Import handling – build the alias table so we can resolve calls like
    #   import numpy as np   ->  np.random.seed  becomes  numpy.random.seed
    # ------------------------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            as_name = alias.asname if alias.asname else alias.name
            self.aliases[as_name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            as_name = alias.asname if alias.asname else alias.name
            full_name = f"{module}.{alias.name}" if module else alias.name
            self.aliases[as_name] = full_name
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Resolve a Call node to a dotted string like "module.function"
    # ------------------------------------------------------------------
    def _resolve_call(self, node: ast.Call) -> str:
        # Handles forms like:
        #   random.seed()
        #   np.random.seed()
        #   myseed.set_seed()
        if isinstance(node.func, ast.Attribute):
            # Walk up the attribute chain to build the full name
            parts: List[str] = []
            attr = node.func
            while isinstance(attr, ast.Attribute):
                parts.append(attr.attr)
                attr = attr.value
            if isinstance(attr, ast.Name):
                root_name = attr.id
                # Resolve possible alias
                root_resolved = self.aliases.get(root_name, root_name)
                parts.append(root_resolved)
            # The parts list is reversed (leaf first)
            return ".".join(reversed(parts))
        elif isinstance(node.func, ast.Name):
            # Simple name – resolve alias if present
            return self.aliases.get(node.func.id, node.func.id)
        return ""

    # ------------------------------------------------------------------
    # Visit each Call node and flag prohibited seed usage
    # ------------------------------------------------------------------
    def visit_Call(self, node: ast.Call) -> None:
        call_str = self._resolve_call(node)

        # If the call is one of the forbidden direct seed functions, record a violation
        if call_str in FORBIDDEN_DIRECT_CALLS:
            # Allow the call if it is wrapped by the project's seed utility (already covered by ALLOWED_SEED_FUNCTIONS)
            if not any(call_str.startswith(allowed.split('.')[0]) for allowed in ALLOWED_SEED_FUNCTIONS):
                self.violations.append(
                    (
                        node.lineno,
                        f"Direct random seed call detected: '{call_str}'. "
                        "Use seeds.get_seed(task_id) or seeds.set_seed instead.",
                    )
                )
        # Continue traversing
        self.generic_visit(node)

# ----------------------------------------------------------------------
# Helper functions for file‑level scanning
# ----------------------------------------------------------------------
def scan_file(filepath: Path) -> List[Tuple[int, str]]:
    """Parse a single Python file and return any seed‑pinning violations."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
        visitor = SeedComplianceVisitor(filepath)
        visitor.visit(tree)
        return visitor.violations
    except SyntaxError as e:
        return [(e.lineno or 0, f"Syntax error: {e.msg}")]
    except Exception as e:
        return [(0, f"Error processing file: {e}")]

def scan_directory(root: Path) -> List[Tuple[Path, List[Tuple[int, str]]]]:
    """Recursively scan ``root`` for ``*.py`` files and collect violations."""
    results: List[Tuple[Path, List[Tuple[int, str]]]] = []
    for py_file in root.rglob("*.py"):
        if "__pycache__" in str(py_file) or py_file.name.startswith("."):
            continue
        violations = scan_file(py_file)
        if violations:
            results.append((py_file, violations))
    return results

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    print(f"Scanning {CODE_ROOT} for seed‑pinning compliance...")

    if not CODE_ROOT.is_dir():
        print(f"Error: Directory '{CODE_ROOT}' does not exist.", file=sys.stderr)
        sys.exit(1)

    violations = scan_directory(CODE_ROOT)

    if not violations:
        print("✅ SUCCESS: All Python files comply with seed pinning (FR-008).")
        sys.exit(0)

    print("❌ FAILURE: Seed pinning violations detected.")
    for file_path, file_violations in violations:
        print(f"\nFile: {file_path}")
        for lineno, msg in file_violations:
            print(f"  Line {lineno}: {msg}")

    print("\n" + "=" * 60)
    print("Please replace direct seed calls with the project's seed utility, e.g.:")
    print("    from utils.seeds import set_seed, get_seed")
    print("    seed = get_seed(task_id)")
    print("    set_seed(seed)")
    print("=" * 60)
    sys.exit(1)

if __name__ == "__main__":
    main()
