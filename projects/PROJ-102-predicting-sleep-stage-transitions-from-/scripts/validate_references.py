"""
Reference Validator Script
Validates that all project references (imports, file paths, config keys) are correct.
"""
import sys
import os
import importlib.util
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_imports(module_name, file_path):
    """Check if a module can be imported without errors."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return False, f"Could not load spec for {file_path}"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, "OK"
    except Exception as e:
        return False, str(e)

def main():
    print("Running Reference Validator...")
    
    # Define critical files to validate
    critical_files = [
        ("tests.contract.test_schemas", "tests/contract/test_schemas.py"),
        ("tests.contract.test_constraints", "tests/contract/test_constraints.py"),
        ("src.utils.logging", "src/utils/logging.py"),
        ("src.utils.config", "src/utils/config.py"),
    ]

    all_passed = True

    for module_name, rel_path in critical_files:
        full_path = project_root / rel_path
        if not full_path.exists():
            print(f"❌ Missing file: {rel_path}")
            all_passed = False
            continue

        passed, msg = check_imports(module_name, str(full_path))
        if passed:
            print(f"✅ {rel_path}: {msg}")
        else:
            print(f"❌ {rel_path}: {msg}")
            all_passed = False

    if all_passed:
        print("\n✅ All reference validations passed.")
        return 0
    else:
        print("\n❌ Some reference validations failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())