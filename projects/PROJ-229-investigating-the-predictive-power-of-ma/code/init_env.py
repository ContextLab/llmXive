import sys
import importlib.util
from pathlib import Path

def check_package(package_name: str) -> bool:
    """
    Check if a specific package is installed.
    
    Args:
        package_name: Name of the package to check.
    
    Returns:
        True if installed, False otherwise.
    """
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def main():
    """
    Verify that all required packages for the pipeline are installed.
    """
    required_packages = [
        "pymatgen",
        "sklearn",
        "pysr",
        "shap",
        "pandas",
        "numpy",
        "matplotlib",
        "requests",
        "yaml", # pyyaml
        "psutil"
    ]

    missing = []
    for pkg in required_packages:
        # Handle specific import name differences
        import_name = pkg
        if pkg == "sklearn":
            import_name = "sklearn"
        elif pkg == "yaml":
            import_name = "yaml"
        
        if not check_package(import_name):
            missing.append(pkg)

    if missing:
        print("Missing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nPlease install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    
    print("All required packages are installed.")
    print(f"Python version: {sys.version}")

if __name__ == "__main__":
    main()
