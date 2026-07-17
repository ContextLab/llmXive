"""
Test that required dependencies are importable and meet minimum version constraints.
"""
import importlib
import sys
from packaging import version

# Define required packages and minimum versions
REQUIRED_PACKAGES = {
    "numpy": "1.24.0",
    "pandas": "2.0.0",
    "nilearn": "0.10.0",
    "networkx": "3.0.0",
    "scikit-learn": "1.2.0",
    "statsmodels": "0.14.0",
    "pingouin": "0.5.0",
    "datasets": "2.14.0",
    "pytest": "7.3.0",
    "jsonschema": "4.17.0",
}

def test_dependencies_installed():
    """Verify all required packages are installed."""
    missing = []
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
        except ImportError:
            missing.append(package)
    
    assert not missing, f"Missing required packages: {missing}"

def test_dependency_versions():
    """Verify installed packages meet minimum version requirements."""
    failed = []
    for package, min_version in REQUIRED_PACKAGES.items():
        try:
            module = importlib.import_module(package)
            # Handle packages where __version__ might be missing or in a different attribute
            if hasattr(module, "__version__"):
                installed_version = module.__version__
            else:
                # Fallback for packages that might not expose __version__ directly
                # In a real scenario, we might use importlib.metadata
                import importlib.metadata
                installed_version = importlib.metadata.version(package)
            
            if version.parse(installed_version) < version.parse(min_version):
                failed.append(f"{package}: {installed_version} < {min_version}")
        except (ImportError, importlib.metadata.PackageNotFoundError) as e:
            failed.append(f"{package}: {str(e)}")
    
    assert not failed, f"Version check failed: {failed}"