"""
Test to verify that all required dependencies are importable.
This ensures the project environment is correctly initialized.
"""
import sys
import importlib

REQUIRED_MODULES = [
    "pandas",
    "numpy",
    "sklearn",
    "nibabel",
    "requests",
    "yaml",
    "statsmodels",
    "scipy",
]

def test_dependencies_available():
    missing = []
    for module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)

    if missing:
        raise ImportError(
            f"The following required dependencies are missing: {', '.join(missing)}. "
            "Please run: pip install -r requirements.txt"
        )

if __name__ == "__main__":
    test_dependencies_available()
    print("All dependencies verified successfully.")
