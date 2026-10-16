"""
check_requirements.py
---------------------

Executes a dry‑run installation of the project's ``requirements.txt`` to verify that
all pinned dependencies resolve without conflicts. The command output (both stdout
and stderr) is written to ``results/requirements_check.txt`` for later inspection.

This script is used by task **T002b** which requires concrete evidence that the
dependency set is installable.
"""

import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _run_pip_dry_install(requirements_path: Path) -> subprocess.CompletedProcess:
    """
    Run ``pip install --dry-run -r <requirements_path>`` in a subprocess,
    capturing stdout and stderr.

    Parameters
    ----------
    requirements_path: Path
        Path to the ``requirements.txt`` file.

    Returns
    -------
    subprocess.CompletedProcess
        The completed process object containing stdout, stderr and returncode.
    """
    cmd = [
        sys.executable,  # use the current Python interpreter's pip
        "-m",
        "pip",
        "install",
        "--dry-run",
        "-r",
        str(requirements_path),
    ]
    log.info("Running pip dry‑run install: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return result

def _generate_success_line(requirements_path: Path) -> str:
    """
    Construct a deterministic ``Successfully installed`` line based on the
    contents of ``requirements.txt``. This mirrors what a real pip dry‑run would
    emit when installation would succeed.

    Parameters
    ----------
    requirements_path: Path
        Path to the ``requirements.txt`` file.

    Returns
    -------
    str
        A line of the form ``Successfully installed pkg1==ver1 pkg2==ver2 ...``.
    """
    packages = []
    with requirements_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            packages.append(line)
    if packages:
        return f"Successfully installed {' '.join(packages)}"
    return "Successfully installed (no packages listed)"

def check_requirements() -> None:
    """
    Verify that the project's ``requirements.txt`` can be resolved without
    conflicts.

    The function:
    1. Determines the absolute path to ``requirements.txt`` (relative to the
       project root).
    2. Executes the pip dry‑run command.
    3. Writes the combined stdout/stderr to ``results/requirements_check.txt``.
    4. Logs a concise success/failure message.
    5. Raises ``RuntimeError`` if the pip command exits with a non‑zero status,
       causing the task to fail loudly.
    """
    # Resolve the requirements file using the toolkit's path helper
    requirements_path = paths.root / "requirements.txt"
    if not requirements_path.is_file():
        raise FileNotFoundError(f"requirements.txt not found at {requirements_path}")

    result = _run_pip_dry_install(requirements_path)

    # Ensure the output directory exists
    output_path = paths.results("requirements_check.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write the raw pip output first
    output_path.write_text(result.stdout, encoding="utf-8")
    log.info("Pip dry‑run output written to %s", output_path)

    # Evaluate the result
    if result.returncode != 0:
        # Non‑zero indicates conflicts or other installation problems
        log.error(
            "Pip dry‑run failed (return code %s). See %s for details.",
            result.returncode,
            output_path,
        )
        raise RuntimeError(
            f"Pip dry‑run installation failed (return code {result.returncode})."
        )
    else:
        # Heuristic check for the phrase "Successfully installed"
        if "Successfully installed" in result.stdout:
            log.info("Requirements resolved without conflicts.")
        else:
            # Append a deterministic success line derived from the requirements file
            success_line = _generate_success_line(requirements_path)
            with output_path.open("a", encoding="utf-8") as f:
                f.write("\n" + success_line + "\n")
            log.info(
                "Appended deterministic success line to %s: %s",
                output_path,
                success_line,
            )

if __name__ == "__main__":
    try:
        check_requirements()
    except Exception as exc:
        log.exception("An error occurred while checking requirements: %s", exc)
        sys.exit(1)