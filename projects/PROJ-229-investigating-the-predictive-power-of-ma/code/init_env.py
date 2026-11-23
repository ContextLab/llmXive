"""
Environment initialization and package verification utility.
Ensures all required dependencies are installed and compatible.
"""
import sys
import importlib.util
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

def check_package(package_name: str, import_name: str = None) -> bool:
    """
    Check if a package is installed and can be imported.

    Args:
        package_name: The name of the package as listed in requirements (e.g., 'scikit-learn')
        import_name: The name used in import statements (e.g., 'sklearn'). Defaults to package_name.

    Returns:
        True if the package is installed and importable, False otherwise.
    """
    if import_name is None:
        # Common mapping for packages with different import names
        mapping = {
            'scikit-learn': 'sklearn',
            'pymatgen': 'pymatgen',
            'pyyaml': 'yaml',
            'matplotlib': 'matplotlib',
            'pysr': 'pysr',
            'requests': 'requests',
            'pandas': 'pandas',
            'numpy': 'np', # Special case for numpy alias
            'shap': 'shap',
            'psutil': 'psutil'
        }
        import_name = mapping.get(package_name, package_name.replace('-', '_'))

    # Special handling for numpy/shap which might need explicit import checks
    if package_name == 'numpy':
        import_name = 'numpy'

    try:
        if import_name == 'np':
            spec = importlib.util.find_spec('numpy')
        else:
            spec = importlib.util.find_spec(import_name)
        
        if spec is None:
            return False
        
        # Attempt a lightweight import to ensure it works
        if import_name == 'np':
            import numpy
        else:
            importlib.import_module(import_name)
        
        return True
    except (ImportError, ModuleNotFoundError, AttributeError):
        return False

def main():
    """
    Main entry point to verify the environment.
    Exits with code 1 if any required package is missing.
    """
    required_packages = [
        "pymatgen",
        "scikit-learn",
        "pysr",
        "shap",
        "pandas",
        "numpy",
        "matplotlib",
        "requests",
        "pyyaml",
        "psutil"
    ]

    missing = []
    print("Checking required dependencies for llmXive PCM Predictive project...")
    
    for pkg in required_packages:
        # Determine import name
        import_name = pkg
        if pkg == 'scikit-learn':
            import_name = 'sklearn'
        elif pkg == 'pyyaml':
            import_name = 'yaml'
        elif pkg == 'numpy':
            import_name = 'numpy' # Check 'numpy' module, not 'np'
        
        is_installed = check_package(pkg, import_name)
        status = "✓" if is_installed else "✗"
        print(f"  {status} {pkg} ({import_name})")
        
        if not is_installed:
            missing.append(pkg)

    if missing:
        print(f"\nERROR: Missing required packages: {', '.join(missing)}")
        print("Please install dependencies using: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\nAll dependencies verified successfully.")
    print(f"Python version: {sys.version}")
    sys.exit(0)

if __name__ == "__main__":
    main()