"""
Refactoring utilities for code cleanup and modularity enforcement.

This module provides tools to analyze, validate, and reorganize the codebase
to ensure modularity, consistent exports, and clean import structures.
"""
import os
import sys
import importlib
import inspect
import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any

# Constants for standard project structure
CODE_ROOT = Path(__file__).resolve().parent.parent
MODULES_TO_ANALYZE = [
    'config',
    'data.models',
    'data.download',
    'data.preprocess_dMRI',
    'data.simulate_EEG',
    'data.quality_control',
    'data.store',
    'analysis.metrics',
    'analysis.avalanches',
    'analysis.fitting',
    'analysis.stats',
    'analysis.sensitivity',
    'analysis.export_metrics',
    'analysis.report',
    'utils.logger',
    'utils.env_config',
    'utils.data_setup',
]

def get_module_functions(module_path: str) -> List[str]:
    """
    Extract all public function names from a module.
    
    Args:
        module_path: Dot-separated module path (e.g., 'data.models')
        
    Returns:
        List of public function names (excluding private and special methods)
    """
    try:
        module = importlib.import_module(module_path)
        functions = []
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith('_'):
                functions.append(name)
        return functions
    except Exception as e:
        print(f"Error analyzing {module_path}: {e}")
        return []

def validate_module_exports(module_path: str) -> Tuple[bool, List[str]]:
    """
    Validate that a module has a consistent __all__ definition.
    
    Args:
        module_path: Dot-separated module path
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    try:
        module = importlib.import_module(module_path)
        if not hasattr(module, '__all__'):
            return False, [f"{module_path} missing __all__ definition"]
        
        defined = set(get_module_functions(module_path))
        exported = set(module.__all__)
        
        issues = []
        for name in exported:
            if name not in defined:
                issues.append(f"{module_path} exports '{name}' but function not found")
        
        return len(issues) == 0, issues
    except Exception as e:
        return False, [f"Error validating {module_path}: {e}"]

def organize_imports(file_path: Path) -> str:
    """
    Reorganize imports in a Python file for consistency.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Refactored file content with organized imports
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    imports = []
    other_lines = []
    in_import_block = False
    current_import_group = []
    
    for line in lines:
        stripped = line.strip()
        
        # Detect import statements
        if stripped.startswith('import ') or stripped.startswith('from '):
            current_import_group.append(line)
            in_import_block = True
        else:
            if in_import_block and current_import_group:
                imports.append(current_import_group)
                current_import_group = []
                in_import_block = False
            other_lines.append(line)
    
    if current_import_group:
        imports.append(current_import_group)
    
    # Sort import groups: stdlib, third-party, local
    stdlib_imports = []
    third_party_imports = []
    local_imports = []
    
    for group in imports:
        for line in group:
            if line.strip().startswith('import '):
                module = line.strip().split('import ')[1].split()[0]
            elif line.strip().startswith('from '):
                module = line.strip().split('from ')[1].split()[0]
            else:
                continue
            
            if module in ['os', 'sys', 'json', 're', 'ast', 'inspect', 'importlib', 'collections', 'typing', 'pathlib', 'math', 'numpy', 'pandas']:
                stdlib_imports.append(line)
            elif module in ['networkx', 'bctpy', 'powerlaw', 'mne', 'matplotlib', 'scipy', 'sklearn', 'dotenv']:
                third_party_imports.append(line)
            else:
                local_imports.append(line)
    
    # Reconstruct file with organized imports
    new_lines = []
    if stdlib_imports:
        new_lines.extend(sorted(stdlib_imports))
        new_lines.append('')
    if third_party_imports:
        new_lines.extend(sorted(third_party_imports))
        new_lines.append('')
    if local_imports:
        new_lines.extend(sorted(local_imports))
        new_lines.append('')
    
    new_lines.extend(other_lines)
    return '\n'.join(new_lines)

def extract_constants(file_path: Path) -> List[Tuple[str, Any]]:
    """
    Extract module-level constants from a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        List of (name, value) tuples for constants
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    constants = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id.isupper():
                        value = None
                        if isinstance(node.value, ast.Constant):
                            value = node.value.value
                        elif isinstance(node.value, ast.List):
                            value = [elt.value if isinstance(elt, ast.Constant) else str(elt) for elt in node.value.elts]
                        constants.append((target.id, value))
    
    return constants

def check_circular_dependencies(modules: List[str]) -> List[Tuple[str, str]]:
    """
    Check for circular dependencies between modules.
    
    Args:
        modules: List of module paths to check
        
    Returns:
        List of (module_a, module_b) tuples indicating circular dependencies
    """
    dependencies = {}
    
    for module_path in modules:
        try:
            module = importlib.import_module(module_path)
            module_file = inspect.getfile(module)
            
            with open(module_file, 'r') as f:
                content = f.read()
            
            deps = set()
            for line in content.split('\n'):
                if line.strip().startswith('from '):
                    try:
                        imported_module = line.strip().split('from ')[1].split()[0]
                        if imported_module in modules and imported_module != module_path:
                            deps.add(imported_module)
                    except:
                        pass
            
            dependencies[module_path] = deps
        except:
            continue
    
    # Detect cycles
    cycles = []
    for mod_a in dependencies:
        for mod_b in dependencies.get(mod_a, []):
            if mod_a in dependencies.get(mod_b, []):
                cycle = tuple(sorted([mod_a, mod_b]))
                if cycle not in [tuple(sorted(c)) for c in cycles]:
                    cycles.append(cycle)
    
    return cycles

def generate_module_documentation(module_path: str) -> str:
    """
    Generate documentation summary for a module.
    
    Args:
        module_path: Dot-separated module path
        
    Returns:
        Documentation string for the module
    """
    try:
        module = importlib.import_module(module_path)
        doc = inspect.getdoc(module) or "No documentation available."
        functions = get_module_functions(module_path)
        
        doc_lines = [
            f"# Module: {module_path}",
            f"",
            f"## Description",
            f"{doc}",
            f"",
            f"## Public Functions",
        ]
        
        for func in sorted(functions):
            func_obj = getattr(module, func)
            func_doc = inspect.getdoc(func_obj) or "No description."
            doc_lines.append(f"- `{func}`: {func_doc.split('.')[0]}.")
        
        return '\n'.join(doc_lines)
    except Exception as e:
        return f"# Error generating documentation for {module_path}: {e}"

def run_refactoring_checks() -> Dict[str, Any]:
    """
    Run all refactoring checks on the project.
    
    Returns:
        Dictionary with check results and recommendations
    """
    results = {
        'module_validation': {},
        'circular_dependencies': [],
        'constants_extracted': {},
        'documentation_generated': {}
    }
    
    print("Running refactoring checks...")
    
    # Validate module exports
    for module_path in MODULES_TO_ANALYZE:
        is_valid, issues = validate_module_exports(module_path)
        results['module_validation'][module_path] = {
            'valid': is_valid,
            'issues': issues
        }
        if not is_valid:
            print(f"  ⚠ {module_path}: {issues}")
        else:
            print(f"  ✓ {module_path}: Valid exports")
    
    # Check circular dependencies
    cycles = check_circular_dependencies(MODULES_TO_ANALYZE)
    results['circular_dependencies'] = cycles
    if cycles:
        print(f"  ⚠ Found {len(cycles)} circular dependencies")
        for c in cycles:
            print(f"    - {c[0]} <-> {c[1]}")
    else:
        print("  ✓ No circular dependencies found")
    
    # Extract constants
    for module_path in MODULES_TO_ANALYZE:
        file_path = CODE_ROOT / f"{module_path.replace('.', '/')}.py"
        if file_path.exists():
            constants = extract_constants(file_path)
            results['constants_extracted'][module_path] = constants
            if constants:
                print(f"  ℹ {module_path}: {len(constants)} constants found")
    
    # Generate documentation
    for module_path in MODULES_TO_ANALYZE:
        doc = generate_module_documentation(module_path)
        results['documentation_generated'][module_path] = doc[:200] + "..."
    
    return results

def main():
    """Main entry point for refactoring utilities."""
    print("=" * 60)
    print("LLMXive Code Refactoring & Modularity Check")
    print("=" * 60)
    
    results = run_refactoring_checks()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    valid_count = sum(1 for v in results['module_validation'].values() if v['valid'])
    total_count = len(results['module_validation'])
    
    print(f"Modules validated: {valid_count}/{total_count}")
    print(f"Circular dependencies: {len(results['circular_dependencies'])}")
    
    if valid_count == total_count and len(results['circular_dependencies']) == 0:
        print("\n✓ All refactoring checks passed!")
        return 0
    else:
        print("\n⚠ Some issues found. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())