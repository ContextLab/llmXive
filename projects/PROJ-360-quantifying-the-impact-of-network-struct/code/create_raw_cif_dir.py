"""
create_raw_cif_dir.py - Ensure the raw CIF directory exists.

This script is a simple preparatory step for the pipeline. It creates the
directory ``data/raw/cif/`` inside the project root using the standard
``llmxive_toolkit.paths`` helpers, which also guarantee that any parent
directories are created.

Running the script is idempotent – if the directory already exists it
will simply do nothing and exit with status 0.
"""
import sys
from llmxive_toolkit import paths

def main() -> int:
    """Create the ``data/raw/cif`` directory."""
    try:
        cif_dir = paths.data("raw", "cif")
        # ``paths.data`` creates the parent folders if they do not exist.
        # The directory itself is created by calling ``mkdir``.
        cif_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {cif_dir}")
        return 0
    except Exception as e:
        print(f"Failed to create directory: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
