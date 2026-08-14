import ast
import re
from typing import List, Dict, Any, Optional, Tuple


def standardize_docstring(docstring: Optional[str]) -> str:
    """Standardize a docstring format."""
    if not docstring:
        return ""
    lines = docstring.strip().split("\n")
    return "\n".join(lines)


def check_imports(file_path: str) -> List[str]:
    """Check for unused imports in a Python file."""
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle attribute access
            pass

    unused = imports - used
    return list(unused)


def remove_unused_imports(file_path: str) -> bool:
    """Remove unused imports from a file."""
    with open(file_path, "r") as f:
        content = f.read()

    unused = check_imports(file_path)
    if not unused:
        return False

    for imp in unused:
        # Remove 'import imp'
        pattern = rf"^\s*import\s+{imp}\s*$"
        content = re.sub(pattern, "", content, flags=re.MULTILINE)
        # Remove 'from ... import imp'
        pattern = rf"^\s*from\s+\S+\s+import\s+.*\b{imp}\b.*$"
        content = re.sub(pattern, "", content, flags=re.MULTILINE)

    with open(file_path, "w") as f:
        f.write(content)

    return True
