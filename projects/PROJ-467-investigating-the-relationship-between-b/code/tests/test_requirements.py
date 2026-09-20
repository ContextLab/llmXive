import importlib
import sys
from pathlib import Path
import pytest

try:
    from packaging import version
except ImportError:
    # Fallback if packaging is not installed in test env (though it should be)
    version = None


def test_dependencies_installed():
    """Verify all required packages in requirements.txt are importable."""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    if not requirements_path.exists():
        pytest.fail("requirements.txt not found at expected path.")

    with open(requirements_path, "r") as f:
        lines = f.readlines()

    required_packages = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Extract package name (ignore version specifiers)
        pkg_name = line.split(">=")[0].split("<")[0].split("==")[0].split("[")[0].strip()
        if pkg_name:
            required_packages.append(pkg_name)

    missing = []
    for pkg in required_packages:
        # Map common package names to import names if they differ
        import_name = pkg
        if pkg == "scikit-learn":
            import_name = "sklearn"
        elif pkg == "nilearn":
            import_name = "nilearn"
        elif pkg == "huggingface-hub":
            import_name = "huggingface_hub"
        elif pkg == "datasets":
            import_name = "datasets"
        
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pkg)

    if missing:
        pytest.fail(f"Missing required dependencies: {', '.join(missing)}")


def test_dependency_versions():
    """Verify installed versions meet minimum requirements (if packaging is available)."""
    if version is None:
        pytest.skip("packaging library not available for version check")

    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    with open(requirements_path, "r") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        pkg_name = line.split(">=")[0].split("<")[0].split("==")[0].split("[")[0].strip()
        if not pkg_name:
            continue

        # Determine import name
        import_name = pkg_name
        if pkg_name == "scikit-learn":
            import_name = "sklearn"
        elif pkg_name == "huggingface-hub":
            import_name = "huggingface_hub"
        
        try:
            pkg_module = importlib.import_module(import_name)
            installed_ver = pkg_module.__version__
            
            # Check minimum version if specified
            if ">=" in line:
                min_ver_str = line.split(">=")[1].split(",")[0].split("<")[0]
                if version.parse(installed_ver) < version.parse(min_ver_str):
                    pytest.fail(f"Package {pkg_name} version {installed_ver} is below required {min_ver_str}")
                    
        except ImportError:
            # Already caught in test_dependencies_installed, but safe to skip here
            pass
        except AttributeError:
            # Some packages don't have __version__
            pass