#!/usr/bin/env python3
"""
Verify FSL and AFNI installation.

Checks for the presence of 'fsl', 'afni', and 'fslmaths' commands in the system PATH.
Exits with code 0 if all tools are present.
Exits with code 1 and prints a clear error message if any tool is missing.
"""
import subprocess
import sys
from pathlib import Path


REQUIRED_TOOLS = ["fsl", "afni", "fslmaths"]


def check_tool_availability(tool_name: str) -> bool:
    """
    Check if a specific tool is available in the system PATH.

    Args:
        tool_name: The name of the command to check.

    Returns:
        True if the tool is found, False otherwise.
    """
    try:
        # Use 'which' on Unix-like systems and 'where' on Windows
        if sys.platform.startswith("win"):
            result = subprocess.run(
                ["where", tool_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        else:
            result = subprocess.run(
                ["which", tool_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        return result.returncode == 0
    except FileNotFoundError:
        # 'which' or 'where' command itself not found (unlikely on standard systems)
        return False


def main():
    """
    Main entry point to verify environment tools.
    """
    missing_tools = []

    for tool in REQUIRED_TOOLS:
        if not check_tool_availability(tool):
            missing_tools.append(tool)

    if missing_tools:
        # Format error message for all missing tools
        missing_str = ", ".join(missing_tools)
        error_msg = (
            f"Required tools not found in PATH: {missing_str}. "
            "Please install FSL/AFNI."
        )
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    # All tools present
    print("All required tools (fsl, afni, fslmaths) are available in PATH.")
    sys.exit(0)


if __name__ == "__main__":
    main()
