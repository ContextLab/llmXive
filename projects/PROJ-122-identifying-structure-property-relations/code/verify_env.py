import sys
import subprocess
import importlib

def check_python_version():
    """Check if the Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        raise RuntimeError(f"Python 3.11+ required. Found {version.major}.{version.minor}")
    return True

def check_dependencies():
    """Check if required dependencies are installed."""
    required = [
        "pandas", "rdkit", "sklearn", "xgboost", "shap", 
        "yaml", "requests", "joblib", "psutil"
    ]
    missing = []
    for pkg in required:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        raise RuntimeError(f"Missing dependencies: {missing}")
    return True

def main():
    """Run environment checks."""
    check_python_version()
    check_dependencies()
    print("Environment check passed.")
