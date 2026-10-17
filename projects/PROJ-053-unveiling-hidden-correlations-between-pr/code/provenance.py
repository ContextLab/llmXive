"""
Provenance script for the project.

This script captures the exact package versions installed in the
current Python environment (via ``pip freeze``) and writes them to a
file under the ``results`` directory. The file can be used to verify
that the environment matches the versions declared in ``requirements.txt``.
"""

import subprocess
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """Run ``pip freeze`` and write the output to ``results/pip_freeze.txt``."""
    try:
        # Capture the output of `pip freeze`
        result = subprocess.run(
            ["pip", "freeze"],
            check=True,
            capture_output=True,
            text=True,
        )
        freeze_output = result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log.error("Failed to execute `pip freeze`: %s", e)
        raise

    # Determine the output path using the project's helper.
    out_path = paths.results("pip_freeze.txt")
    out_path.write_text(freeze_output + "\n")
    log.info("Wrote pip freeze output to %s", out_path)

if __name__ == "__main__":
    main()
