"""
linting_setup.py
----------------
Small convenience wrapper that can be invoked from the command line to
ensure that Ruff and Black are installed and that the project's
``pyproject.toml`` contains the appropriate configuration sections.
"""
import sys
from pathlib import Path

from config_linting import main as config_main

def check_tool(tool_name: str) -> bool:
    """
    Returns ``True`` if ``tool_name`` can be executed (i.e. is on PATH).
    """
    import subprocess

    try:
        subprocess.run(
            [tool_name, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_tool(tool_name: str) -> bool:
    """
    Attempts to install ``tool_name`` via ``pip``.  Returns ``True`` if the
    installation command exits with status 0.
    """
    import subprocess

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", tool_name],
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def main() -> int:
    """
    Runs the configuration routine from ``config_linting`` and, if either
    tool is missing, attempts a pip install.
    """
    exit_code = config_main()
    # If configuration succeeded, we are done.
    if exit_code == 0:
        return 0

    # Otherwise try to install missing tools.
    missing = [t for t in ("ruff", "black") if not check_tool(t)]
    if not missing:
        # Configuration failed for a reason other than missing tools.
        return exit_code

    print(f"Attempting to install missing tools: {', '.join(missing)}")
    for tool in missing:
        if not install_tool(tool):
            print(f"Failed to install {tool}.", file=sys.stderr)
            return 1
    # Re‑run the configuration after installation.
    return config_main()

if __name__ == "__main__":
    sys.exit(main())
