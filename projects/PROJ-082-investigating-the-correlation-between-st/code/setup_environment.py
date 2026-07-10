import sys
import subprocess
import pkg_resources

def check_python_version():
    """Check if Python version is 3.11+."""
    if sys.version_info < (3, 11):
        print(f"Error: Python 3.11+ required. Current: {sys.version}")
        sys.exit(1)
    print(f"Python version check passed: {sys.version}")

def check_dependencies():
    """Check if required dependencies are installed."""
    required = [
        'pandas', 'numpy', 'scipy', 'statsmodels', 
        'matplotlib', 'seaborn', 'pyyaml'
    ]
    missing = []
    for pkg in required:
        try:
            pkg_resources.get_distribution(pkg)
        except pkg_resources.DistributionNotFound:
            missing.append(pkg)
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)
    print("All dependencies check passed.")

def main():
    check_python_version()
    check_dependencies()

if __name__ == "__main__":
    main()
