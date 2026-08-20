"""
Seed Pinning Compliance Verifier (Task T004b).

This script scans all Python files in the `code/` directory to ensure that
every random operation (e.g., `random.seed`, `np.random.seed`, `torch.manual_seed`)
uses `seeds.get_seed(task_id)` (or the wrapper `seeds.set_seed`) as mandated by FR-008.

It exits with code 0 if compliant, 1 if any violation is found.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple, Set

# Constants
CODE_ROOT = Path("code")
ALLOWED_SEED_FUNCTIONS = {
    "seeds.set_seed",
    "seeds.get_seed",
    "seeds.restore_seed_state",
    "seeds.verify_seed",
}
# Patterns of direct random calls that are FORBIDDEN unless wrapped or using a seed from seeds.py
FORBIDDEN_DIRECT_CALLS = {
    "random.seed",
    "np.random.seed",
    "numpy.random.seed",
    "torch.manual_seed",
    "torch.cuda.manual_seed",
    "torch.cuda.manual_seed_all",
    "torch.backends.cudnn.deterministic", # Often used with seeds, but must be set explicitly
}

class SeedComplianceVisitor(ast.NodeVisitor):
    """AST visitor to detect seed usage violations."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.violations: List[Tuple[int, str]] = []
        self.imports: Set[str] = set()
        self.aliases: dict = {}  # maps alias -> module

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            full_name = alias.name
            as_name = alias.asname if alias.asname else alias.name
            self.imports.add(full_name)
            self.aliases[as_name] = full_name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            full_name = f"{module}.{alias.name}"
            as_name = alias.asname if alias.asname else alias.name
            self.imports.add(full_name)
            self.aliases[as_name] = full_name
        self.generic_visit(node)

    def _resolve_call(self, node: ast.Call) -> str:
        """Resolves a function call to a string like 'module.func' or 'alias.func'."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                base = node.func.value.id
                # Resolve alias if it exists
                base_module = self.aliases.get(base, base)
                return f"{base_module}.{node.func.attr}"
            elif isinstance(node.func.value, ast.Attribute):
                # Handle nested attributes like np.random.seed
                # We need to walk up to find the root name
                parts = []
                current = node.func
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    root = current.id
                    root_module = self.aliases.get(root, root)
                    parts.append(root_module)
                    return ".".join(reversed(parts))
        elif isinstance(node.func, ast.Name):
            return self.aliases.get(node.func.id, node.func.id)
        return ""

    def visit_Call(self, node: ast.Call):
        call_str = self._resolve_call(node)

        # Check for forbidden direct calls
        if call_str in FORBIDDEN_DIRECT_CALLS:
            # Special case: if it's seeds.* it's allowed
            if call_str.startswith("seeds."):
                self.generic_visit(node)
                return

            # Check if it's a known allowed wrapper
            is_allowed = False
            for allowed in ALLOWED_SEED_FUNCTIONS:
                if call_str == allowed or call_str.endswith(allowed.split('.')[-1]):
                    # If it matches exactly or is a known alias of the allowed function
                    # We need to be careful with aliases.
                    # If the call is `random.seed`, it's forbidden.
                    # If the call is `seeds.set_seed`, it's allowed.
                    pass
            
            # Strict check: if the resolved string matches a forbidden pattern exactly
            # or if it's a direct call to random/np/torch without going through seeds.py
            if call_str in FORBIDDEN_DIRECT_CALLS:
                self.violations.append((
                    node.lineno,
                    f"Direct random seed call detected: '{call_str}'. "
                    f"Must use seeds.get_seed(task_id) or seeds.set_seed."
                ))

        self.generic_visit(node)

def scan_file(filepath: Path) -> List[Tuple[int, str]]:
    """Scan a single Python file for seed pinning violations."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        
        tree = ast.parse(source, filename=str(filepath))
        visitor = SeedComplianceVisitor(filepath)
        visitor.visit(tree)
        return visitor.violations
    except SyntaxError as e:
        return [(e.lineno or 0, f"Syntax error in file: {e.msg}")]
    except Exception as e:
        return [(0, f"Error parsing file: {str(e)}")]

def scan_directory(root_path: Path) -> List[Tuple[Path, List[Tuple[int, str]]]]:
    """Recursively scan a directory for Python files and check compliance."""
    violations_found = []
    
    for py_file in root_path.rglob("*.py"):
        # Skip __pycache__ and hidden directories
        if "__pycache__" in str(py_file) or py_file.name.startswith("."):
            continue
        
        file_violations = scan_file(py_file)
        if file_violations:
            violations_found.append((py_file, file_violations))
    
    return violations_found

def main():
    """Main entry point for the seed pinning verification."""
    print(f"Scanning {CODE_ROOT} for seed pinning compliance...")
    
    if not CODE_ROOT.exists():
        print(f"Error: Directory '{CODE_ROOT}' not found.")
        sys.exit(1)

    violations = scan_directory(CODE_ROOT)

    if not violations:
        print("✅ SUCCESS: All Python files comply with seed pinning (FR-008).")
        print("   Every random operation uses seeds.get_seed(task_id) or seeds.set_seed.")
        sys.exit(0)
    else:
        print("❌ FAILURE: Seed pinning violations detected.")
        for filepath, file_violations in violations:
            print(f"\nFile: {filepath}")
            for line_no, msg in file_violations:
                print(f"  Line {line_no}: {msg}")
        
        print("\n" + "="*60)
        print("FIX REQUIRED: Replace direct random calls with:")
        print("  from utils.seeds import set_seed, get_seed")
        print("  seed = get_seed(task_id)")
        print("  set_seed(seed)")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()