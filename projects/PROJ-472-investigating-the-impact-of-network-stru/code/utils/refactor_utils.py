"""
Refactoring utilities for code cleanup and modularity enforcement.

This module provides tools to analyze code structure, validate exports,
organize imports, and enforce modular design patterns across the pipeline.
"""
import os
import sys
import importlib
import inspect
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from collections import defaultdict

# Import from project utils
from .logger import get_logger, log_exception

logger = get_logger(__name__)


def get_module_functions(module_path: str) -> Dict[str, List[str]]:
    """
    Extract all public functions and classes from a module.
    
    Args:
        module_path: Path to the module (e.g., 'analysis.metrics')
        
    Returns:
        Dictionary mapping function/class names to their docstrings
    """
    try:
        # Convert path to module name
        module_name = module_path.replace('/', '.').replace('\\', '.')
        if module_name.endswith('.py'):
            module_name = module_name[:-3]
        
        # Import the module
        module = importlib.import_module(module_name)
        
        results = {
            'functions': [],
            'classes': [],
            'constants': []
        }
        
        # Iterate through module members
        for name, obj in inspect.getmembers(module):
            # Skip private and built-in names
            if name.startswith('_'):
                continue
            
            if inspect.isfunction(obj):
                doc = inspect.getdoc(obj) or ""
                results['functions'].append({
                    'name': name,
                    'docstring': doc,
                    'signature': str(inspect.signature(obj))
                })
            elif inspect.isclass(obj):
                doc = inspect.getdoc(obj) or ""
                results['classes'].append({
                    'name': name,
                    'docstring': doc,
                    'methods': [m for m, _ in inspect.getmembers(obj) 
                               if not m.startswith('_') and callable(_)]
                })
            elif isinstance(obj, (str, int, float, bool, list, dict, tuple)):
                results['constants'].append({
                    'name': name,
                    'type': type(obj).__name__,
                    'value': repr(obj) if len(repr(obj)) < 100 else repr(obj)[:100] + '...'
                })
        
        return results
        
    except ImportError as e:
        logger.error(f"Failed to import module {module_path}: {e}")
        return {'functions': [], 'classes': [], 'constants': []}
    except Exception as e:
        log_exception(e)
        return {'functions': [], 'classes': [], 'constants': []}


def validate_module_exports(module_path: str, expected_exports: List[str]) -> Dict[str, Any]:
    """
    Validate that a module exports the expected public names.
    
    Args:
        module_path: Path to the module
        expected_exports: List of expected public function/class names
        
    Returns:
        Dictionary with validation results
    """
    try:
        module_name = module_path.replace('/', '.').replace('\\', '.')
        if module_name.endswith('.py'):
            module_name = module_name[:-3]
        
        module = importlib.import_module(module_name)
        actual_exports = set()
        
        for name in dir(module):
            if not name.startswith('_'):
                actual_exports.add(name)
        
        missing = set(expected_exports) - actual_exports
        extra = actual_exports - set(expected_exports)
        
        return {
            'valid': len(missing) == 0,
            'missing': list(missing),
            'extra': list(extra),
            'actual': list(actual_exports)
        }
        
    except Exception as e:
        log_exception(e)
        return {'valid': False, 'missing': expected_exports, 'extra': [], 'actual': []}


def organize_imports(file_path: str) -> str:
    """
    Organize imports in a Python file: standard library, third-party, local.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        File content with organized imports
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST
        tree = ast.parse(content)
        
        # Separate imports
        stdlib_imports = []
        third_party_imports = []
        local_imports = []
        
        # Known standard library modules (comprehensive list)
        stdlib_modules = {
            'os', 'sys', 'pathlib', 'typing', 'collections', 'itertools',
            'functools', 'operator', 'dataclasses', 'json', 'csv', 're',
            'logging', 'datetime', 'time', 'hashlib', 'random', 'math',
            'numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn',
            'networkx', 'powerlaw', 'mne', 'sklearn', 'statsmodels',
            'pytest', 'unittest', 'argparse', 'subprocess', 'shutil',
            'tempfile', 'io', 'pickle', 'copy', 'string', 'textwrap',
            'warnings', 'contextlib', 'abc', 'enum', 'graphlib'
        }
        
        # Extract imports from AST
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    import_line = f"import {alias.name}"
                    if module_name in stdlib_modules or module_name in {'numpy', 'pandas', 'networkx', 'matplotlib', 'scipy', 'sklearn', 'mne', 'powerlaw'}:
                        third_party_imports.append(import_line)
                    else:
                        stdlib_imports.append(import_line)
                        
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                module_name = module.split('.')[0] if module else ''
                
                if module.startswith('.'):
                    # Relative import
                    local_imports.append(
                        f"from {''.join('.' * node.level)}{module} import "
                        f"{', '.join(alias.name for alias in node.names)}"
                    )
                elif module_name in stdlib_modules:
                    stdlib_imports.append(
                        f"from {module} import "
                        f"{', '.join(alias.name for alias in node.names)}"
                    )
                else:
                    third_party_imports.append(
                        f"from {module} import "
                        f"{', '.join(alias.name for alias in node.names)}"
                    )
        
        # Sort and deduplicate
        stdlib_imports = sorted(set(stdlib_imports))
        third_party_imports = sorted(set(third_party_imports))
        local_imports = sorted(set(local_imports))
        
        # Reconstruct content
        lines = content.split('\n')
        new_lines = []
        
        # Add organized imports
        if stdlib_imports:
            new_lines.extend(stdlib_imports)
            new_lines.append('')
        
        if third_party_imports:
            new_lines.extend(third_party_imports)
            new_lines.append('')
        
        if local_imports:
            new_lines.extend(local_imports)
            new_lines.append('')
        
        # Add rest of the file (skip original import lines)
        in_import_block = False
        for line in lines:
            stripped = line.strip()
            
            # Detect import block
            if stripped.startswith('import ') or stripped.startswith('from '):
                if not in_import_block:
                    in_import_block = True
                continue
            elif in_import_block and stripped == '':
                continue
            elif in_import_block and not (stripped.startswith('import ') or stripped.startswith('from ')):
                in_import_block = False
                new_lines.append(line)
            elif not in_import_block:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
        
    except Exception as e:
        log_exception(e)
        return None


def extract_constants(file_path: str) -> List[Dict[str, Any]]:
    """
    Extract module-level constants from a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        List of constant definitions
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content)
        constants = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        # Check if it looks like a constant (uppercase)
                        if name.isupper() or (name.endswith('_') and name[:-1].isupper()):
                            try:
                                value = ast.literal_eval(node.value)
                                constants.append({
                                    'name': name,
                                    'value': value,
                                    'type': type(value).__name__,
                                    'line': node.lineno
                                })
                            except (ValueError, TypeError):
                                # Not a literal, skip
                                pass
        
        return constants
        
    except Exception as e:
        log_exception(e)
        return []


def check_circular_dependencies(module_paths: List[str]) -> List[Tuple[str, str]]:
    """
    Check for circular dependencies between modules.
    
    Args:
        module_paths: List of module paths to check
        
    Returns:
        List of tuples representing circular dependencies
    """
    # Build dependency graph
    dependencies = defaultdict(set)
    
    for module_path in module_paths:
        try:
            module_name = module_path.replace('/', '.').replace('\\', '.')
            if module_name.endswith('.py'):
                module_name = module_name[:-3]
            
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                    if module and module.startswith('.'):
                        # Relative import - resolve
                        parts = module_name.split('.')
                        depth = node.level
                        base = parts[:-depth] if depth <= len(parts) else []
                        resolved = '.'.join(base + [module[1:]]) if module[1:] else '.'.join(base)
                        if resolved:
                            dependencies[module_name].add(resolved)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if '.' in alias.name and alias.name.startswith('.'):
                            dependencies[module_name].add(alias.name)
        
        except Exception as e:
            logger.warning(f"Could not analyze {module_path}: {e}")
    
    # Detect cycles using DFS
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: str, path: List[str]) -> bool:
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor, path + [neighbor]):
                    return True
            elif neighbor in rec_stack:
                # Found cycle
                cycle_start = path.index(neighbor) if neighbor in path else -1
                if cycle_start >= 0:
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(tuple(cycle))
                return True
        
        rec_stack.remove(node)
        return False
    
    for module in dependencies:
        if module not in visited:
            dfs(module, [module])
    
    return cycles


def generate_module_documentation(module_path: str) -> str:
    """
    Generate documentation for a module based on its structure.
    
    Args:
        module_path: Path to the module
        
    Returns:
        Markdown documentation string
    """
    try:
        module_info = get_module_functions(module_path)
        module_name = Path(module_path).stem
        
        doc_lines = [
            f"# Module: {module_name}",
            "",
            "## Overview",
            "",
            f"Module `{module_name}` provides the following functionality:",
            ""
        ]
        
        # Document functions
        if module_info['functions']:
            doc_lines.append("### Functions")
            doc_lines.append("")
            for func in module_info['functions']:
                doc_lines.append(f"- **`{func['name']}{func['signature']}`**: {func['docstring'][:100]}...")
            doc_lines.append("")
        
        # Document classes
        if module_info['classes']:
            doc_lines.append("### Classes")
            doc_lines.append("")
            for cls in module_info['classes']:
                doc_lines.append(f"- **`{cls['name']}`**: {cls['docstring'][:100]}...")
                if cls['methods']:
                    doc_lines.append(f"  - Methods: {', '.join(cls['methods'][:5])}")
            doc_lines.append("")
        
        # Document constants
        if module_info['constants']:
            doc_lines.append("### Constants")
            doc_lines.append("")
            for const in module_info['constants']:
                doc_lines.append(f"- `{const['name']}`: {const['value']}")
            doc_lines.append("")
        
        return '\n'.join(doc_lines)
        
    except Exception as e:
        log_exception(e)
        return f"# Module: {Path(module_path).stem}\n\n*Documentation generation failed*"


def run_refactoring_checks(project_root: str, target_dirs: List[str]) -> Dict[str, Any]:
    """
    Run comprehensive refactoring checks on the project.
    
    Args:
        project_root: Root directory of the project
        target_dirs: List of directories to analyze
        
    Returns:
        Dictionary with refactoring report
    """
    report = {
        'modules_analyzed': 0,
        'issues_found': [],
        'recommendations': [],
        'circular_dependencies': [],
        'missing_docstrings': []
    }
    
    # Find all Python files
    python_files = []
    for target_dir in target_dirs:
        full_path = os.path.join(project_root, target_dir)
        if os.path.exists(full_path):
            for root, _, files in os.walk(full_path):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))
    
    report['modules_analyzed'] = len(python_files)
    
    # Analyze each module
    for file_path in python_files:
        try:
            # Check for missing docstrings
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            module_doc = ast.get_docstring(tree)
            
            if not module_doc:
                report['missing_docstrings'].append(file_path)
                report['issues_found'].append({
                    'file': file_path,
                    'issue': 'Missing module docstring',
                    'severity': 'warning'
                })
            
            # Check functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        report['missing_docstrings'].append(f"{file_path}:{node.name}")
        
        except Exception as e:
            report['issues_found'].append({
                'file': file_path,
                'issue': f"Analysis failed: {e}",
                'severity': 'error'
            })
    
    # Check for circular dependencies
    module_paths = [os.path.relpath(f, project_root) for f in python_files]
    cycles = check_circular_dependencies(module_paths)
    report['circular_dependencies'] = [list(c) for c in cycles]
    
    # Generate recommendations
    if report['missing_docstrings']:
        report['recommendations'].append(
            f"Add docstrings to {len(report['missing_docstrings'])} functions/modules"
        )
    
    if report['circular_dependencies']:
        report['recommendations'].append(
            f"Resolve {len(report['circular_dependencies'])} circular dependencies"
        )
    
    if not report['issues_found']:
        report['recommendations'].append("No major issues found. Code is well-structured.")
    
    return report


def main():
    """
    Main entry point for refactoring utility.
    Runs analysis on the project and prints a summary report.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Code refactoring and modularity checker')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--dirs', nargs='+', default=['code', 'tests'], 
                       help='Directories to analyze')
    parser.add_argument('--organize-imports', action='store_true',
                       help='Organize imports in all Python files')
    parser.add_argument('--generate-docs', action='store_true',
                       help='Generate documentation for all modules')
    parser.add_argument('--output', default='refactoring_report.json',
                       help='Output file for report')
    
    args = parser.parse_args()
    
    logger.info(f"Starting refactoring analysis on {args.project_root}")
    
    # Run checks
    report = run_refactoring_checks(args.project_root, args.dirs)
    
    # Organize imports if requested
    if args.organize_imports:
        python_files = []
        for target_dir in args.dirs:
            full_path = os.path.join(args.project_root, target_dir)
            if os.path.exists(full_path):
                for root, _, files in os.walk(full_path):
                    for file in files:
                        if file.endswith('.py'):
                            python_files.append(os.path.join(root, file))
        
        organized_count = 0
        for file_path in python_files:
            new_content = organize_imports(file_path)
            if new_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                organized_count += 1
                logger.info(f"Organized imports in {file_path}")
        
        report['imports_organized'] = organized_count
    
    # Generate docs if requested
    if args.generate_docs:
        doc_count = 0
        for target_dir in args.dirs:
            full_path = os.path.join(args.project_root, target_dir)
            if os.path.exists(full_path):
                for root, _, files in os.walk(full_path):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, args.project_root)
                            doc = generate_module_documentation(rel_path)
                            if doc and not doc.startswith("*Documentation generation failed"):
                                doc_count += 1
        
        report['docs_generated'] = doc_count
    
    # Save report
    import json
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Refactoring report saved to {args.output}")
    print(json.dumps(report, indent=2))
    
    return report


if __name__ == '__main__':
    main()