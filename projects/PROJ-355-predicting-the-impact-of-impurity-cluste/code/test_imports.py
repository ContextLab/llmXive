"""
Script to verify that all packages listed in requirements.txt are installed
and can be imported successfully.
"""
import sys
import importlib

# List of packages to verify based on requirements.txt
packages = [
    "pymatgen",
    "scikit-learn",
    "statsmodels",
    "numpy",
    "pandas",
    "ase",
    "requests",
    "pyyaml",
    "pytest",
    "ruff",
    "black",
]

# Additional specific modules that are commonly imported
# to ensure the core functionality is accessible
specific_imports = [
    ("pymatgen.core", "Structure"),
    ("sklearn.linear_model", "LinearRegression"),
    ("statsmodels.api", "OLS"),
    ("pandas", "DataFrame"),
    ("numpy", "array"),
    ("ase.calculators.eam", "EAM"),
    ("yaml", "safe_load"),
]

def verify_package(pkg_name: str) -> bool:
    """Attempt to import a package and return success status."""
    try:
        importlib.import_module(pkg_name)
        print(f"✓ {pkg_name} imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import {pkg_name}: {e}")
        return False

def verify_specific_import(module_name: str, symbol: str) -> bool:
    """Attempt to import a specific symbol from a module."""
    try:
        module = importlib.import_module(module_name)
        getattr(module, symbol)
        print(f"✓ {module_name}.{symbol} accessible")
        return True
    except (ImportError, AttributeError) as e:
        print(f"✗ Failed to access {module_name}.{symbol}: {e}")
        return False

def main():
    print("Verifying package imports for PROJ-355...")
    print("-" * 40)

    all_success = True

    # Check main packages
    for pkg in packages:
        if not verify_package(pkg):
            all_success = False

    print("-" * 40)
    print("Verifying specific module symbols...")
    print("-" * 40)

    # Check specific imports
    for module, symbol in specific_imports:
        if not verify_specific_import(module, symbol):
            all_success = False

    print("-" * 40)
    if all_success:
        print("All imports verified successfully.")
        return 0
    else:
        print("Some imports failed. Please check your environment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())