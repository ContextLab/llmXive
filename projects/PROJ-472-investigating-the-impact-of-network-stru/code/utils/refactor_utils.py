"""
Refactoring utilities to improve modularity and code organization.

This module provides helper functions and classes to support the cleanup
and refactoring of the llmXive research pipeline, ensuring better separation
of concerns and maintainability.
"""
import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
import logging

from .logger import get_logger

logger = get_logger(__name__)


def get_module_functions(module_path: str) -> Dict[str, Callable]:
    """
    Extract all public functions from a given module.
    
    Args:
        module_path: Path to the module (e.g., 'code.analysis.metrics')
        
    Returns:
        Dictionary mapping function names to function objects
    """
    try:
        module = importlib.import_module(module_path)
        functions = {}
        
        for name, obj in inspect.getmembers(module):
            if (inspect.isfunction(obj) and 
                not name.startswith('_') and 
                hasattr(module, name)):
                functions[name] = obj
        
        logger.info(f"Extracted {len(functions)} public functions from {module_path}")
        return functions
        
    except ImportError as e:
        logger.error(f"Failed to import module {module_path}: {e}")
        return {}


def validate_module_exports(module_path: str, expected_exports: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that a module exports all expected public names.
    
    Args:
        module_path: Path to the module
        expected_exports: List of expected public function/class names
        
    Returns:
        Tuple of (success, missing_names)
    """
    try:
        module = importlib.import_module(module_path)
        missing = []
        
        for name in expected_exports:
            if not hasattr(module, name):
                missing.append(name)
        
        success = len(missing) == 0
        if not success:
            logger.warning(f"Module {module_path} missing exports: {missing}")
        else:
            logger.info(f"Module {module_path} has all expected exports")
            
        return success, missing
        
    except ImportError as e:
        logger.error(f"Failed to import module {module_path} for validation: {e}")
        return False, expected_exports


def organize_imports(file_path: str) -> bool:
    """
    Organize and clean up imports in a Python file.
    
    This function reads a Python file, separates imports into standard library,
    third-party, and local imports, then rewrites the file with organized imports.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        standard_lib = []
        third_party = []
        local_imports = []
        other_lines = []
        
        in_import_section = False
        current_section = None
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('import ') or stripped.startswith('from '):
                in_import_section = True
                
                # Determine import type
                if 'code.' in line or 'data.' in line or 'analysis.' in line or 'utils.' in line:
                    local_imports.append(line)
                elif any(pkg in line for pkg in ['numpy', 'pandas', 'matplotlib', 'networkx', 'powerlaw', 'mne', 'scipy', 'sklearn', 'bctpy', 'dotenv']):
                    third_party.append(line)
                else:
                    standard_lib.append(line)
            else:
                if in_import_section and not stripped:
                    continue  # Skip blank lines in import section
                in_import_section = False
                other_lines.append(line)
        
        # Reconstruct file with organized imports
        organized_lines = []
        
        if standard_lib:
            organized_lines.extend(standard_lib)
            organized_lines.append('')
        
        if third_party:
            organized_lines.extend(third_party)
            organized_lines.append('')
        
        if local_imports:
            organized_lines.extend(local_imports)
            organized_lines.append('')
        
        organized_lines.extend(other_lines)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(organized_lines))
        
        logger.info(f"Organized imports in {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to organize imports in {file_path}: {e}")
        return False


def extract_constants(module_path: str) -> Dict[str, Any]:
    """
    Extract module-level constants from a Python file.
    
    Args:
        module_path: Path to the module
        
    Returns:
        Dictionary of constant names and values
    """
    try:
        module = importlib.import_module(module_path)
        constants = {}
        
        for name in dir(module):
            if name.isupper() or (name.startswith('DEFAULT_') or name.startswith('CONFIG_')):
                value = getattr(module, name)
                if not callable(value):
                    constants[name] = value
        
        logger.info(f"Extracted {len(constants)} constants from {module_path}")
        return constants
        
    except Exception as e:
        logger.error(f"Failed to extract constants from {module_path}: {e}")
        return {}


def check_circular_dependencies(module_paths: List[str]) -> List[Tuple[str, str]]:
    """
    Check for circular dependencies between modules.
    
    Args:
        module_paths: List of module paths to check
        
    Returns:
        List of tuples representing circular dependencies
    """
    dependencies = {}
    
    for module_path in module_paths:
        try:
            module = importlib.import_module(module_path)
            deps = []
            
            for name, obj in inspect.getmembers(module):
                if inspect.ismodule(obj):
                    deps.append(obj.__name__)
            
            dependencies[module_path] = deps
        except Exception:
            continue
    
    # Simple circular dependency detection
    circular = []
    for mod1, deps1 in dependencies.items():
        for mod2, deps2 in dependencies.items():
            if mod1 != mod2 and mod1 in deps2 and mod2 in deps1:
                pair = tuple(sorted([mod1, mod2]))
                if pair not in [tuple(sorted(c)) for c in circular]:
                    circular.append(pair)
    
    if circular:
        logger.warning(f"Found {len(circular)} circular dependencies: {circular}")
    else:
        logger.info("No circular dependencies detected")
        
    return circular


def generate_module_documentation(module_path: str, output_path: str) -> bool:
    """
    Generate documentation for a module based on its public API.
    
    Args:
        module_path: Path to the module
        output_path: Path to write documentation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        module = importlib.import_module(module_path)
        
        doc_lines = [
            f"# Module Documentation: {module_path}",
            "",
            f"**Module**: `{module_path}`",
            f"**Docstring**: {module.__doc__ or 'No docstring available'}",
            "",
            "## Public API",
            ""
        ]
        
        for name, obj in inspect.getmembers(module):
            if (not name.startswith('_') and 
                (inspect.isfunction(obj) or inspect.isclass(obj))):
                
                doc_lines.append(f"### {name}")
                doc_lines.append(f"**Type**: {'Function' if inspect.isfunction(obj) else 'Class'}")
                
                if obj.__doc__:
                    doc_lines.append(f"**Docstring**: {obj.__doc__.strip()}")
                
                if inspect.isfunction(obj):
                    sig = inspect.signature(obj)
                    doc_lines.append(f"**Signature**: `{name}{sig}`")
                
                doc_lines.append("")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(doc_lines))
        
        logger.info(f"Generated documentation for {module_path} at {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate documentation for {module_path}: {e}")
        return False


def run_refactoring_checks(project_root: str) -> Dict[str, Any]:
    """
    Run a comprehensive set of refactoring checks on the project.
    
    Args:
        project_root: Root directory of the project
        
    Returns:
        Dictionary with check results and recommendations
    """
    results = {
        'circular_dependencies': [],
        'missing_exports': [],
        'unorganized_imports': [],
        'recommendations': []
    }
    
    # Define key modules to check
    key_modules = [
        'code.analysis.metrics',
        'code.analysis.avalanches',
        'code.analysis.fitting',
        'code.analysis.stats',
        'code.data.models',
        'code.data.store',
        'code.data.quality_control',
        'code.config',
        'code.utils.logger'
    ]
    
    # Check for circular dependencies
    results['circular_dependencies'] = check_circular_dependencies(key_modules)
    
    # Check expected exports
    expected_exports = {
        'code.analysis.metrics': ['compute_degree_centrality', 'compute_clustering_coefficient', 
                                  'compute_rich_club_coefficient', 'run_metrics_pipeline', 'main'],
        'code.analysis.avalanches': ['z_score_normalize', 'calculate_threshold', 'detect_avalanches',
                                     'run_avalanche_detection_for_subject', 'run_avalanche_pipeline', 'main'],
        'code.data.models': ['Participant', 'StructuralConnectome', 'AvalancheRecord'],
        'code.config': ['get_data_root', 'ensure_directories']
    }
    
    for module, exports in expected_exports.items():
        success, missing = validate_module_exports(module, exports)
        if not success:
            results['missing_exports'].append({
                'module': module,
                'missing': missing
            })
            results['recommendations'].append(f"Add missing exports to {module}: {missing}")
    
    # Check for unorganized imports
    python_files = list(Path(project_root).rglob('*.py'))
    for py_file in python_files[:20]:  # Check first 20 Python files
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple heuristic: check if imports are mixed
            lines = content.split('\n')
            import_lines = [l for l in lines if l.strip().startswith('import ') or l.strip().startswith('from ')]
            
            if len(import_lines) > 3:
                # Check if there are blank lines between different import types
                has_gaps = any(not l.strip() for l in import_lines)
                if not has_gaps:
                    results['unorganized_imports'].append(str(py_file))
                    results['recommendations'].append(f"Organize imports in {py_file}")
                    
        except Exception:
            continue
    
    logger.info(f"Refactoring checks complete. Found {len(results['recommendations'])} recommendations.")
    return results


def main():
    """Main entry point for refactoring utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Refactoring utilities for llmXive project')
    parser.add_argument('--check', action='store_true', help='Run refactoring checks')
    parser.add_argument('--project-root', default='.', help='Project root directory')
    parser.add_argument('--module', type=str, help='Specific module to analyze')
    parser.add_argument('--doc-output', type=str, help='Output path for module documentation')
    
    args = parser.parse_args()
    
    if args.check:
        results = run_refactoring_checks(args.project_root)
        print("Refactoring Check Results:")
        print(f"  Circular Dependencies: {len(results['circular_dependencies'])}")
        print(f"  Missing Exports: {len(results['missing_exports'])}")
        print(f"  Unorganized Imports: {len(results['unorganized_imports'])}")
        print(f"  Recommendations: {len(results['recommendations'])}")
        
        if results['recommendations']:
            print("\nRecommendations:")
            for rec in results['recommendations']:
                print(f"  - {rec}")
                
    elif args.module:
        if args.doc_output:
            success = generate_module_documentation(args.module, args.doc_output)
            if success:
                print(f"Documentation generated at {args.doc_output}")
            else:
                print("Failed to generate documentation")
        else:
            functions = get_module_functions(args.module)
            print(f"Public functions in {args.module}:")
            for name in functions:
                print(f"  - {name}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()