"""
API Documentation Generator for llmXive SpatialClaw Project.

This module generates API documentation for the code/kernel/ module,
extracting docstrings, function signatures, and class definitions.
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

from kernel.blockers import RestrictedActionError, check_library_policy
from kernel.restricted_kernel import (
    RestrictedImportHook,
    RestrictedKernel,
    get_kernel,
    enforce_2d_policy,
    release_2d_policy,
)

def get_module_info(module: Any) -> Dict[str, Any]:
    """Extract public API information from a module."""
    info = {
        "name": module.__name__,
        "doc": inspect.getdoc(module) or "",
        "functions": [],
        "classes": [],
        "exceptions": [],
    }

    for name, obj in inspect.getmembers(module):
        if name.startswith("_"):
            continue

        if inspect.isfunction(obj) or inspect.isbuiltin(obj):
            sig = str(inspect.signature(obj)) if hasattr(obj, "__signature__") else ""
            doc = inspect.getdoc(obj) or ""
            info["functions"].append({
                "name": name,
                "signature": sig,
                "doc": doc,
            })

        elif inspect.isclass(obj):
            sig = str(inspect.signature(obj)) if hasattr(obj, "__init__") else ""
            doc = inspect.getdoc(obj) or ""
            methods = []
            for method_name, method in inspect.getmembers(obj, predicate=inspect.isfunction):
                if method_name.startswith("_") and method_name != "__init__":
                    continue
                method_sig = str(inspect.signature(method)) if hasattr(method, "__signature__") else ""
                method_doc = inspect.getdoc(method) or ""
                methods.append({
                    "name": method_name,
                    "signature": method_sig,
                    "doc": method_doc,
                })

            # Determine if it's an exception
            if issubclass(obj, BaseException):
                info["exceptions"].append({
                    "name": name,
                    "signature": sig,
                    "doc": doc,
                    "methods": methods,
                })
            else:
                info["classes"].append({
                    "name": name,
                    "signature": sig,
                    "doc": doc,
                    "methods": methods,
                })

    return info

def format_markdown(info: Dict[str, Any]) -> str:
    """Format module info as Markdown documentation."""
    lines = []
    lines.append(f"# Module: {info['name']}")
    lines.append("")
    if info["doc"]:
        lines.append(info["doc"])
        lines.append("")

    if info["exceptions"]:
        lines.append("## Exceptions")
        lines.append("")
        for exc in info["exceptions"]:
            lines.append(f"### `{exc['name']}`")
            lines.append("")
            if exc["doc"]:
                lines.append(exc["doc"])
                lines.append("")
            lines.append("")

    if info["classes"]:
        lines.append("## Classes")
        lines.append("")
        for cls in info["classes"]:
            lines.append(f"### `{cls['name']}`")
            lines.append("")
            if cls["doc"]:
                lines.append(cls["doc"])
                lines.append("")
            lines.append("```python")
            lines.append(f"class {cls['name']}{cls['signature']}:")
            lines.append("```")
            lines.append("")
            if cls["methods"]:
                lines.append("**Methods:**")
                lines.append("")
                for method in cls["methods"]:
                    lines.append(f"- `{method['name']}{method['signature']}`")
                    if method["doc"]:
                        lines.append(f"  - {method['doc'].split(chr(10))[0]}")
                lines.append("")

    if info["functions"]:
        lines.append("## Functions")
        lines.append("")
        for func in info["functions"]:
            lines.append(f"### `{func['name']}{func['signature']}`")
            lines.append("")
            if func["doc"]:
                lines.append(func["doc"])
                lines.append("")
    return "\n".join(lines)

def generate_kernel_docs(output_path: Optional[str] = None) -> str:
    """Generate API documentation for the code/kernel/ module."""
    modules = [
        ("kernel.blockers", "Blockers - Library Whitelist/Blacklist"),
        ("kernel.restricted_kernel", "Restricted Kernel - Import Interception"),
    ]

    all_docs = []
    all_docs.append("# API Documentation: code/kernel/")
    all_docs.append("")
    all_docs.append("This document provides the API reference for the kernel module,")
    all_docs.append("which enforces the 2D spatial reasoning restriction policy.")
    all_docs.append("")

    for module_name, title in modules:
        try:
            module = importlib.import_module(module_name)
            info = get_module_info(module)
            module_doc = format_markdown(info)
            all_docs.append(f"## {title}")
            all_docs.append("")
            all_docs.append(module_doc)
            all_docs.append("")
        except ImportError as e:
            all_docs.append(f"## {title}")
            all_docs.append("")
            all_docs.append(f"*Module could not be imported: {e}*")
            all_docs.append("")

    full_doc = "\n".join(all_docs)

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_doc)

    return full_doc

def main():
    """Main entry point for generating API docs."""
    output_dir = project_root / "docs"
    output_path = output_dir / "api" / "kernel.md"

    print(f"Generating API documentation for code/kernel/ module...")
    doc_content = generate_kernel_docs(str(output_path))

    print(f"Documentation generated successfully at: {output_path}")
    print(f"Total characters: {len(doc_content)}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
