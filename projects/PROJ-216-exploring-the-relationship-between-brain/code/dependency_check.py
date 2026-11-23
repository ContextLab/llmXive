"""
System-level dependency check script for FSL/AFNI availability.

This module provides functions to verify the presence and executability
of critical neuroimaging tools (FSL, AFNI) required for the preprocessing pipeline.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


def run_command(command: List[str], timeout: int = 30) -> Tuple[bool, str]:
    """
    Execute a shell command and return success status and output.

    Args:
        command: List of command arguments.
        timeout: Maximum time to wait for the command to complete (seconds).

    Returns:
        Tuple of (success: bool, output: str).
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        output = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return False, "Command not found in PATH"
    except Exception as e:
        return False, str(e)


def check_tool_availability(tool_name: str, version_args: List[str]) -> Dict[str, Any]:
    """
    Check if a specific tool is available and retrieve its version.

    Args:
        tool_name: Name of the tool (e.g., 'fsl_version', 'afni_version').
        version_args: Arguments to pass to the tool to get version info.

    Returns:
        Dictionary with availability status and version info.
    """
    success, output = run_command(version_args)

    if success:
        return {
            "available": True,
            "version": output,
            "error": None
        }
    else:
        return {
            "available": False,
            "version": None,
            "error": output
        }


def check_all_tools() -> Dict[str, Any]:
    """
    Check availability of all required neuroimaging tools.

    Returns:
        Dictionary containing status for FSL and AFNI.
    """
    results = {
        "fsl": check_tool_availability("fsl", ["fslversion"]),
        "afni": check_tool_availability("afni", ["afni", "-ver"]),
        "summary": {}
    }

    fsl_ok = results["fsl"]["available"]
    afni_ok = results["afni"]["available"]

    results["summary"]["all_available"] = fsl_ok and afni_ok
    results["summary"]["fsl_required"] = True
    results["summary"]["afni_required"] = True

    if not fsl_ok:
        results["summary"]["missing_tools"] = results["summary"].get("missing_tools", []) + ["FSL"]
    if not afni_ok:
        results["summary"]["missing_tools"] = results["summary"].get("missing_tools", []) + ["AFNI"]

    return results


def main() -> int:
    """
    Main entry point for the dependency check script.

    Returns:
        Exit code: 0 if all dependencies are met, 1 otherwise.
    """
    print("Checking system dependencies for neuroimaging pipeline...")
    print("-" * 50)

    results = check_all_tools()

    # Print results
    for tool, status in results.items():
        if tool == "summary":
            continue
        status_str = "✓ Available" if status["available"] else "✗ Missing"
        print(f"{tool.upper()}: {status_str}")
        if status["version"]:
            print(f"  Version: {status['version'][:100]}...")
        if status["error"]:
            print(f"  Error: {status['error'][:100]}...")

    print("-" * 50)
    summary = results["summary"]

    if summary["all_available"]:
        print("All required dependencies are installed.")
        return 0
    else:
        missing = ", ".join(summary.get("missing_tools", []))
        print(f"CRITICAL: Missing required dependencies: {missing}")
        print("Please install FSL and/or AFNI and ensure they are in your PATH.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
