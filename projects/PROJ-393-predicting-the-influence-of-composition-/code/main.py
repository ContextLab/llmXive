"""
Top‑level script used by the quickstart guide.
Delegates to the package entry point defined in ``src/main.py``.
"""
import sys

def _run():
    # Import the package entry point and forward the command‑line arguments.
    from src.main import main as src_main
    # ``sys.argv[1:]`` contains any flags passed to this script.
    return src_main(sys.argv[1:])

if __name__ == "__main__":
    sys.exit(_run())
