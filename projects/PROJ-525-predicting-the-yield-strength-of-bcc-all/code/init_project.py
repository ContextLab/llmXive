import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Ensure Python 3.11+ is being used."""
    if sys.version_info < (3, 11):
        raise RuntimeError("Python 3.11 or higher is required.")

def check_dependencies():
    """Verify that all required packages are installed."""
    required = [
        "pandas==2.2.2",
        "numpy==1.26.4",
        "scikit-learn==1.5.0",
        "scipy==1.13.0",
        "periodictable==1.6.1",
        "requests==2.32.3",
        "pyyaml==6.0.2",
        "ruff==0.5.0",
        "black==24.3.0",
    ]
    missing = []
    for pkg in required:
        name = pkg.split("==")[0]
        try:
            __import__(name)
        except ImportError:
            missing.append(pkg)
    if missing:
        raise RuntimeError(f"Missing dependencies: {missing}")

def check_dev_tools():
    """Check that development tools (ruff, black) are available."""
    for tool in ["ruff", "black"]:
        try:
            subprocess.run([tool, "--version"], check=True, stdout=subprocess.DEVNULL)
        except Exception:
            raise RuntimeError(f"Development tool {tool} not found in PATH.")

def main():
    """Run all project initialization checks."""
    check_python_version()
    check_dependencies()
    check_dev_tools()
    print("All checks passed.")

if __name__ == "__main__":
    main()
