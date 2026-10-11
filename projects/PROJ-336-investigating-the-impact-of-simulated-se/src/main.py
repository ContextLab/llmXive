"""
Proxy entry point for `python -m src.main`.

The actual pipeline implementation lives in `code/main.py`. This thin wrapper
loads that module at runtime and forwards the `main()` call, preserving the
original CLI interface (including `--dry-run`, `--sample`, etc.).
"""
import importlib.util
import sys
from pathlib import Path

def _load_code_main():
    """
    Dynamically load the implementation module located at `code/main.py`.
    Returns the loaded module object.
    """
    code_main_path = Path(__file__).resolve().parents[1] / "code" / "main.py"
    if not code_main_path.is_file():
        raise FileNotFoundError(f"Implementation not found at {code_main_path}")

    spec = importlib.util.spec_from_file_location("code_main", str(code_main_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module

# Load the real implementation once at import time
_CODE_MAIN = _load_code_main()

def main():
    """
    Forward the call to the real `main` function defined in `code/main.py`.
    Returns the exit code from the underlying implementation.
    """
    return _CODE_MAIN.main()

if __name__ == "__main__":
    sys.exit(main())
