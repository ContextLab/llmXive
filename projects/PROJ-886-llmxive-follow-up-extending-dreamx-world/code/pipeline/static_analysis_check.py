"""
Static Analysis Check for Evaluation Pipeline Integrity.

This script verifies that code/pipeline/evaluate.py does not import
restricted model internals (dit_attention, latent_space, etc.).

This is used in CI to enforce the "Blindness" constraint of User Story 4.
"""

import ast
import sys
import os
from pathlib import Path

# Restricted imports that violate the separation of concerns
RESTRICTED_IMPORTS = {
    "dit_attention",
    "latent_space",
    "dreamx_base", # Only the base loader is allowed, not internals
    "dreamx_lite", # Only the lite loader is allowed, not internals
    "DiT",
    "Attention",
    "backbone"
}

# Allowed imports from model modules (high-level loaders only)
ALLOWED_MODEL_IMPORTS = {
    "create_dreamx_base_model",
    "create_dreamx_lite_model"
}

def check_file_integrity(file_path: str) -> bool:
    """
    Parses a Python file and checks for restricted imports.
    
    Args:
        file_path: Path to the Python file to check.
        
    Returns:
        True if the file passes the check, False otherwise.
    """
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return False
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"ERROR: Syntax error in {file_path}: {e}")
        return False
        
    violations = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in RESTRICTED_IMPORTS:
                    violations.append(f"Restricted import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.module in RESTRICTED_IMPORTS:
                    violations.append(f"Restricted import from: {node.module}")
                # Check specific names imported from allowed modules
                if node.module in ["models.dreamx_base", "models.dreamx_lite"]:
                    for alias in node.names:
                        if alias.name in RESTRICTED_IMPORTS:
                            violations.append(f"Restricted import from {node.module}: {alias.name}")
                            # Note: We allow create_dreamx_base_model, etc.
                            # But we block internal attributes like 'dit_attention'
    
    if violations:
        print(f"FAILED: Static analysis violations found in {file_path}:")
        for v in violations:
            print(f"  - {v}")
        return False
        
    print(f"PASSED: {file_path} is clean.")
    return True

def main():
    # Determine the project root relative to this script
    # Assuming this script is in code/pipeline/
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    evaluate_file = project_root / "code" / "pipeline" / "evaluate.py"
    
    print(f"Checking integrity of: {evaluate_file}")
    
    if check_file_integrity(str(evaluate_file)):
        print("Static analysis check PASSED.")
        sys.exit(0)
    else:
        print("Static analysis check FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
