"""
Quick‑start validation script.

In the original repository this script lived at ``code/run_quickstart_validation.py``.
It has been migrated to ``code/scripts/`` to keep maintenance utilities separate
from the research code.
"""

import sys
import subprocess

def main() -> None:
    """
    Execute the project's quick‑start validation suite.

    The command simply runs the pytest marker ``quickstart`` which the
    repository's CI uses to verify that the pipeline can be executed
    from a clean checkout.
    """
    try:
        subprocess.run([sys.executable, "-m", "pytest", "-m", "quickstart", "-v"], check=True)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)

if __name__ == "__main__":
    main()
