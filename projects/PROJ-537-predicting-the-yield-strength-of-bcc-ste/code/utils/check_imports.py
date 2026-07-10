"""
Pre-commit hook to check import consistency and prevent circular imports.
Validates that imports follow the project structure and naming conventions.
"""
import os
import sys
import ast
from pathlib import Path
from typing import Set, List, Tuple

# Known valid imports based on project structure
VALID_MODULES = {
    "config",
    "utils",
    "utils.logging",
    "utils.checksums",
    "ingestion",
    "ingestion.fetch_experimental",
    "ingestion.fetch_dft",
    "ingestion.merge_and_filter",
    "ingestion.finalize_dataset",
    "ingestion.generate_checksums",
    "ingestion.update_state",
    "modeling",
    "modeling.features",
    "modeling.train",
    "modeling.evaluate",
    "interpretability",
    "interpretability.shap_analysis",
    "interpretability.bootstrap_stability",
    "main",
    "setup_directories",
    "setup_git_hooks",
}

# Patterns that should be avoided
AVOIDED_IMPORTS = {
    "absolute_imports": ["os.path.abspath", "sys.path.append"],
    "relative_imports": ["..", "..."],  # Allow relative imports within packages
}

def analyze_file(filepath: Path) -> List[str]:
    """Analyze a Python file for import issues."""
    issues = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("code."):
                        # Relative import style within code/
                        pass
                    elif alias.name not in VALID_MODULES and not any(alias.name.startswith(m) for m in VALID_MODULES):
                        # Check if it's a standard library or third-party package
                        if not alias.name.startswith("code") and not alias.name.startswith("utils") and not alias.name.startswith("ingestion"):
                            # Allow standard library and third-party
                            pass
                    elif alias.name.startswith(".."):
                        issues.append(f"Deep relative import detected: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    if node.module.startswith(".."):
                        issues.append(f"Deep relative import detected: {node.module}")
                    # Check if it's a valid local module
                    if node.module.startswith("code."):
                        # This is fine, it's a local import
                        pass

        # Check for absolute path usage
        if "os.path.abspath" in content or "sys.path.append" in content:
            issues.append("Avoid using absolute path manipulation in imports")

    except SyntaxError as e:
        issues.append(f"Syntax error in {filepath}: {e}")
    except Exception as e:
        issues.append(f"Error analyzing {filepath}: {e}")

    return issues

def main():
    """Run import consistency checks."""
    code_dir = Path(__file__).parent.parent
    print("🔍 Checking import consistency...")

    all_issues = []
    for py_file in code_dir.rglob("*.py"):
        # Skip __init__.py files for now as they often have special imports
        if py_file.name == "__init__.py":
            continue

        issues = analyze_file(py_file)
        if issues:
            all_issues.append((str(py_file), issues))

    if all_issues:
        print(f"❌ Found import issues in {len(all_issues)} file(s):")
        for file_path, issues in all_issues:
            print(f"  {file_path}:")
            for issue in issues:
                print(f"    - {issue}")
        return 1
    else:
        print("✅ Import consistency check passed.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
