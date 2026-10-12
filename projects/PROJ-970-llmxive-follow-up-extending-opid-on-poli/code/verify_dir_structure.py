"""
verify_dir_structure.py

This script verifies the project directory structure by invoking the
external ``tree`` command (depth limited to 2) from the project root and
writing its output to ``data/processed/dir_structure.txt``.

It is used to satisfy task **T001a** which requires capturing the
directory tree listing.
"""
import subprocess
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def main() -> None:
    """
    Execute ``tree -L 2`` in the repository root and write the output
    to ``data/processed/dir_structure.txt``.
    """
    root_path = paths.root
    log.info("Running `tree -L 2` on project root: %s", root_path)

    # Run the external ``tree`` command. ``check=True`` raises an error
    # if the command fails (e.g., ``tree`` not installed), which is
    # desirable because we must not silently fallback to synthetic data.
    result = subprocess.run(
        ["tree", "-L", "2", str(root_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    output_path = paths.data("processed", "dir_structure.txt")
    output_path.write_text(result.stdout)
    log.info("Directory structure written to %s", output_path)

if __name__ == "__main__":
    main()
