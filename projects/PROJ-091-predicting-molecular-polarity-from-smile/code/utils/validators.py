"""
Runtime validators for enforcing 2D-only molecular processing.

This module provides functions to assert that no 3D-dependent 
operations (like conformer generation or 3D distance calculations)
are performed during descriptor computation or model training.
"""
import sys
import types
from typing import Callable, Set, Optional
import inspect

# List of forbidden 3D functions
FORBIDDEN_3D_FUNCTIONS = {
    'EmbedMolecule',
    'EmbedMultipleConfs',
    'MMFFOptimizeMolecule',
    'UFFOptimizeMolecule',
    'Get3DDistance',
    'Get3DDistanceMatrix',
    'Compute2DDepth',
}

# Forbidden 3D modules
FORBIDDEN_3D_MODULES = {
    'rdkit.Chem.rdForceFieldHelpers',
    'rdkit.Chem.rdDistGeom',
}

def enforce_2d_only_imports(module: types.ModuleType) -> bool:
    """
    Enforce that a module only imports 2D-safe RDKit components.
    
    Args:
        module: The module to check.
        
    Returns:
        True if all imports are 2D-safe, False otherwise.
    """
    # Check imports in the module's namespace
    for name, obj in inspect.getmembers(module):
        if inspect.ismodule(obj):
            full_name = f"{module.__name__}.{name}"
            for forbidden in FORBIDDEN_3D_MODULES:
                if forbidden in full_name:
                    return False
    return True

def assert_no_3d_calls(module_name: str) -> None:
    """
    Assert that a module's source code does not call forbidden 3D functions.
    
    Args:
        module_name: The name of the module to check.
        
    Raises:
        AssertionError: If any forbidden 3D functions are found in the source.
        ModuleNotFoundError: If the module cannot be found.
    """
    try:
        module = sys.modules.get(module_name)
        if module is None:
            # Try to import it
            import importlib
            module = importlib.import_module(module_name)
        
        # Get source code
        source = inspect.getsource(module)
        
        # Check for forbidden function calls
        for func in FORBIDDEN_3D_FUNCTIONS:
            if f'.{func}(' in source or f'AllChem.{func}(' in source:
                raise AssertionError(
                    f"Module {module_name} calls forbidden 3D function: {func}"
                )
                
        # Check for forbidden module imports
        for mod in FORBIDDEN_3D_MODULES:
            if f'import {mod}' in source or f'from {mod}' in source:
                raise AssertionError(
                    f"Module {module_name} imports forbidden 3D module: {mod}"
                )
                
    except ImportError:
        raise ModuleNotFoundError(f"Module {module_name} not found")

def validate_descriptor_computation_context(context: dict) -> bool:
    """
    Validate that the descriptor computation context is 2D-only.
    
    Args:
        context: Dictionary containing computation context information.
        
    Returns:
        True if context is 2D-only, False otherwise.
    """
    # Check for 3D-related keys
    forbidden_keys = ['conformer', '3d', 'force_field', 'optimization']
    for key in context.get('options', {}).keys():
        if any(f in key.lower() for f in forbidden_keys):
            return False
    return True
