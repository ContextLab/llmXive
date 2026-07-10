"""
Basic sanity check to ensure all pinned dependencies in requirements.txt
can be imported successfully.
"""
import sys

def test_imports():
    """Verify core dependencies are installed and importable."""
    required_modules = [
        "numpy",
        "pandas",
        "networkx",
        "scipy",
        "statsmodels",
        "matplotlib",
        "seaborn",
        "yaml",
        "tqdm",
        "pytest",
    ]

    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        raise ImportError(
            f"Missing required dependencies: {', '.join(missing)}. "
            "Please run 'pip install -r requirements.txt'."
        )

    # Verify Python version
    if sys.version_info < (3, 11):
        raise RuntimeError(
            f"Python 3.11+ is required. Current version: {sys.version}"
        )

    print("All dependencies verified successfully.")