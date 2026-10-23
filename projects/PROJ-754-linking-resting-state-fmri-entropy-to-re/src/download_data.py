"""
Wrapper module that forwards the CLI invocation to the real implementation
in ``code.src.data.download_hcp``.  Keeping this thin shim inside a top‑level
``src`` package satisfies the historic run‑book commands (e.g.
``python -m src.download_data``) without having to modify the existing
quick‑start documentation.
"""
import importlib
import sys

def main() -> None:
    """
    Import and execute the actual download routine.
    """
    module = importlib.import_module("code.src.data.download_hcp")
    module.main()

if __name__ == "__main__":
    main()
