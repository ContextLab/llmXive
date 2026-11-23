"""
API Documentation Generator for code/agents/ module.

This script inspects the agent modules (agent_2d.py and baseline_3d.py)
and generates a comprehensive Markdown API documentation file.
"""
import os
import sys
import inspect
import importlib
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.agent_2d import Agent2D, run_agent_on_dataset, main as main_2d
from agents.baseline_3d import Baseline3DAgent, run_baseline_on_dataset, main as main_3d

def get_module_info(module: Any) -> Dict[str, Any]:
    """Extract public classes and functions from a module."""
    classes = []
    functions = []

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            # Skip private/internal classes
            if not name.startswith('_'):
                classes.append({
                    'name': name,
                    'doc': inspect.getdoc(obj) or 'No documentation available.',
                    'methods': []
                })
                # Get methods
                for method_name, method_obj in inspect.getmembers(obj, predicate=inspect.isfunction):
                    if not method_name.startswith('_') or method_name in ['__init__']:
                        sig = str(inspect.signature(method_obj)) if inspect.signature(method_obj) else ''
                        doc = inspect.getdoc(method_obj) or 'No documentation available.'
                        classes[-1]['methods'].append({
                            'name': method_name,
                            'signature': sig,
                            'doc': doc
                        })

        elif inspect.isfunction(obj) and obj.__module__ == module.__name__:
            if not name.startswith('_'):
                sig = str(inspect.signature(obj)) if inspect.signature(obj) else ''
                doc = inspect.getdoc(obj) or 'No documentation available.'
                functions.append({
                    'name': name,
                    'signature': sig,
                    'doc': doc
                })

    return {
        'classes': classes,
        'functions': functions
    }

def format_markdown(module_name: str, info: Dict[str, Any]) -> str:
    """Format module info as Markdown."""
    lines = [f"## Module: `{module_name}`", ""]

    if info['classes']:
        lines.append("### Classes")
        lines.append("")
        for cls in info['classes']:
            lines.append(f"#### `{cls['name']}`")
            lines.append("")
            lines.append(cls['doc'])
            lines.append("")
            if cls['methods']:
                lines.append("**Methods:**")
                lines.append("")
                for method in cls['methods']:
                    lines.append(f"- `{method['name']}{method['signature']}`")
                    lines.append(f"  - {method['doc']}")
                    lines.append("")

    if info['functions']:
        lines.append("### Functions")
        lines.append("")
        for func in info['functions']:
            lines.append(f"#### `{func['name']}{func['signature']}`")
            lines.append("")
            lines.append(func['doc'])
            lines.append("")

    return "\n".join(lines)

def generate_agents_docs() -> str:
    """Generate API docs for the agents module."""
    title = "# API Documentation: Agents Module\n"
    intro = """
    This document provides the API reference for the `code/agents/` module,
    which contains the restricted 2D agent and the 3D baseline agent implementations.
    """

    docs = [title, intro, ""]

    # Process agent_2d.py
    docs.append(format_markdown("agents.agent_2d", get_module_info(sys.modules['agents.agent_2d'])))
    docs.append("")

    # Process baseline_3d.py
    docs.append(format_markdown("agents.baseline_3d", get_module_info(sys.modules['agents.baseline_3d'])))
    docs.append("")

    return "\n".join(docs)

def main():
    """Main entry point to generate and save API docs."""
    output_dir = PROJECT_ROOT / "docs"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "agents_api.md"

    print(f"Generating API documentation for agents module...")
    docs_content = generate_agents_docs()

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(docs_content)

    print(f"API documentation written to: {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())