import sys
import types
from typing import Callable, Set, Optional
import inspect

# Forbidden 3D functions
FORBIDDEN_3D = {
    "EmbedMolecule",
    "Get3DConformer",
    "Compute2DDepth",
    "CalcMolDescriptors3D"
}

def enforce_2d_only_imports(module: types.ModuleType) -> bool:
    """Enforce 2D-only imports by checking for forbidden functions."""
    for name in FORBIDDEN_3D:
        if hasattr(module, name):
            return False
    return True

def assert_no_3d_calls(code_str: str) -> bool:
    """Assert no 3D calls in code string."""
    for func in FORBIDDEN_3D:
        if func in code_str:
            return False
    return True

def validate_descriptor_computation_context(context: dict) -> bool:
    """Validate descriptor computation context."""
    if "use_3d" in context and context["use_3d"]:
        return False
    return True
