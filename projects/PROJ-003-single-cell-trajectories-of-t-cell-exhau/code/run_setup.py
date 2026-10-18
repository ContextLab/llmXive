"""High‑level setup entry point.

The script installs the SRA Toolkit (if needed) and creates the
project directory layout. It is intended to be called from the quick‑start
``bash code/setup_lint.sh`` script before any analysis runs.
"""

import sys

from install_sra_toolkit import main as install_sra
from init_project import main as init_proj


def main() -> None:
    """Run the full environment bootstrap."""
    # Install and verify the SRA Toolkit.
    try:
        install_sra()
    except Exception as exc:
        sys.stderr.write(f"SRA Toolkit setup failed: {exc}\\n")
        sys.exit(1)

    # Create the directory layout.
    try:
        init_proj()
    except Exception as exc:
        sys.stderr.write(f"Project layout creation failed: {exc}\\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
