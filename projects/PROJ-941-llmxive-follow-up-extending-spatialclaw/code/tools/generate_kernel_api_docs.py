"""
Generate API documentation for the code/kernel/ module.

This script inspects the kernel modules (blockers.py, restricted_kernel.py)
and generates a comprehensive Markdown API reference.
"""
import os
import sys
import inspect
import importlib
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def get_module_info(module_name: str) -> Dict[str, Any]:
    """
    Inspect a module and extract public classes, functions, and their signatures.
    """
    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        return {
            "name": module_name,
            "error": f"Failed to import: {e}",
            "classes": [],
            "functions": [],
            "constants": []
        }

    docs = {
        "name": module_name,
        "doc": inspect.getdoc(module) or "No module docstring.",
        "classes": [],
        "functions": [],
        "constants": []
    }

    for name, obj in inspect.getmembers(module):
        if name.startswith('_'):
            continue

        # Classes
        if inspect.isclass(obj):
            cls_info = {
                "name": name,
                "doc": inspect.getdoc(obj) or "No docstring.",
                "methods": []
            }
            for method_name, method_obj in inspect.getmembers(obj, predicate=inspect.isfunction):
                if method_name.startswith('_'):
                    continue
                sig = str(inspect.signature(method_obj))
                doc = inspect.getdoc(method_obj) or "No docstring."
                cls_info["methods"].append({
                    "name": method_name,
                    "signature": sig,
                    "doc": doc
                })
            docs["classes"].append(cls_info)

        # Functions
        elif inspect.isfunction(obj):
            sig = str(inspect.signature(obj))
            doc = inspect.getdoc(obj) or "No docstring."
            docs["functions"].append({
                "name": name,
                "signature": sig,
                "doc": doc
            })

        # Constants (simple variables)
        elif not inspect.ismodule(obj) and not inspect.isclass(obj) and not inspect.isfunction(obj):
            # Heuristic: if it's not a complex type, treat as constant
            if isinstance(obj, (int, float, str, bool, type(None))):
                docs["constants"].append({
                    "name": name,
                    "value": repr(obj)
                })

    return docs

def format_markdown(module_info: Dict[str, Any]) -> str:
    """
    Format module info into a Markdown string.
    """
    lines = []
    lines.append(f"# Module: {module_info['name']}")
    lines.append("")
    lines.append(module_info["doc"])
    lines.append("")

    if "error" in module_info:
        lines.append(f"> **Error**: {module_info['error']}")
        return "\n".join(lines)

    # Constants
    if module_info["constants"]:
        lines.append("## Constants")
        lines.append("")
        for const in module_info["constants"]:
            lines.append(f"- `{const['name']}`: `{const['value']}`")
        lines.append("")

    # Classes
    if module_info["classes"]:
        lines.append("## Classes")
        lines.append("")
        for cls in module_info["classes"]:
            lines.append(f"### `{cls['name']}`")
            lines.append("")
            lines.append(cls["doc"])
            lines.append("")
            if cls["methods"]:
                lines.append("**Methods**:")
                lines.append("")
                for method in cls["methods"]:
                    lines.append(f"- `{method['name']}{method['signature']}`")
                    lines.append(f"  - {method['doc']}")
                lines.append("")

    # Functions
    if module_info["functions"]:
        lines.append("## Functions")
        lines.append("")
        for func in module_info["functions"]:
            lines.append(f"### `{func['name']}{func['signature']}`")
            lines.append("")
            lines.append(func["doc"])
            lines.append("")

    return "\n".join(lines)

def generate_kernel_docs() -> str:
    """
    Generate API documentation for all modules in code/kernel/.
    """
    kernel_path = project_root / "code" / "kernel"
    if not kernel_path.exists():
        return f"# Error\n\nKernel module path not found: {kernel_path}"

    docs = []
    docs.append("# API Documentation: code/kernel/")
    docs.append("")
    docs.append("This document provides the API reference for the `code/kernel/` module,")
    docs.append("which implements the restricted execution environment for SpatialClaw.")
    docs.append("")
    docs.append("---")
    docs.append("")

    modules_to_scan = [
        "code.kernel.blockers",
        "code.kernel.restricted_kernel"
    ]

    for mod_name in modules_to_scan:
        info = get_module_info(mod_name)
        docs.append(format_markdown(info))
        docs.append("---")
        docs.append("")

    return "\n".join(docs)

def main():
    """
    Entry point for generating kernel API docs.
    """
    output_path = project_root / "docs" / "api_kernel.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = generate_kernel_docs()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"API documentation generated at: {output_path}")

if __name__ == "__main__":
    main()