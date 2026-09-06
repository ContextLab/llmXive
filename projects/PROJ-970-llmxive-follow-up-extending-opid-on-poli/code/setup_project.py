"""
Script to verify and display the project setup status.
Runs after T002 to confirm dependencies are resolved and environment is ready.
"""
import sys
import importlib
import os

def check_dependency(name: str, import_name: str = None):
    """Check if a dependency is installed and importable."""
    if import_name is None:
        import_name = name
    try:
        mod = importlib.import_module(import_name)
        return True, mod.__version__ if hasattr(mod, '__version__') else "installed"
    except ImportError:
        return False, None

def main():
    print("=== llmXive Project Setup Verification (T002) ===")
    print(f"Python Version: {sys.version}")
    print("-" * 40)

    deps = [
        ("networkx", "networkx"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("scipy", "scipy"),
        ("pytest", "pytest"),
    ]

    all_ok = True
    for name, imp_name in deps:
        ok, version = check_dependency(name, imp_name)
        status = "OK" if ok else "MISSING"
        print(f"[{status}] {name:12} (v{version})")
        if not ok:
            all_ok = False

    print("-" * 40)
    
    # Check files
    files = ["requirements.txt", "pyproject.toml", "code/__init__.py"]
    for f in files:
        exists = os.path.isfile(f)
        status = "OK" if exists else "MISSING"
        print(f"[{status}] {f}")
        if not exists:
            all_ok = False

    if all_ok:
        print("\n✅ Project setup complete. All dependencies and structures verified.")
        return 0
    else:
        print("\n❌ Project setup incomplete. Missing dependencies or files.")
        return 1

if __name__ == "__main__":
    sys.exit(main())