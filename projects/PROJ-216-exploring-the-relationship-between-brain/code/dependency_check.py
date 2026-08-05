import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def run_command(command: List[str], timeout: int = 30) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Execute a system command and return success status, stdout, and stderr.
    
    Args:
        command: List of command arguments.
        timeout: Maximum time in seconds to wait for the command to complete.
        
    Returns:
        Tuple of (success: bool, stdout: str | None, stderr: str | None)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        success = result.returncode == 0
        return success, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, None, f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return False, None, f"Command not found: {command[0]}"
    except Exception as e:
        return False, None, str(e)

def check_tool_availability(tool_name: str, version_command: List[str]) -> Dict[str, Any]:
    """
    Check if a specific tool is available and retrieve its version.
    
    Args:
        tool_name: Name of the tool (e.g., 'fsl', 'afni').
        version_command: Command list to get the version (e.g., ['fslversion']).
        
    Returns:
        Dictionary with keys: 'available' (bool), 'version' (str | None), 'error' (str | None)
    """
    success, stdout, stderr = run_command(version_command)
    
    if success:
        # Clean up version string (remove newlines)
        version = stdout.strip() if stdout else "Unknown version"
        return {
            "available": True,
            "version": version,
            "error": None
        }
    else:
        return {
            "available": False,
            "version": None,
            "error": stderr or "Command failed or not found"
        }

def check_all_tools() -> Dict[str, Dict[str, Any]]:
    """
    Check availability of all required system dependencies (FSL, AFNI).
    
    Returns:
        Dictionary mapping tool names to their availability status.
    """
    results = {}
    
    # Check FSL
    # FSL typically provides 'fslversion' command. If not, we check for 'fsl' executable.
    fsl_check = check_tool_availability("fsl", ["fslversion"])
    if not fsl_check["available"]:
        # Fallback: check if 'fsl' command exists (some installations)
        fsl_check = check_tool_availability("fsl", ["which", "fsl"])
        if fsl_check["available"]:
            fsl_check["version"] = "Installed (version check via fslversion failed)"
        else:
            fsl_check["available"] = False
            fsl_check["error"] = "FSL not found. Please ensure FSL is installed and in PATH."
    results["FSL"] = fsl_check
    
    # Check AFNI
    # AFNI typically provides 'afni_version' or '3dinfo' command.
    afni_check = check_tool_availability("afni", ["afni_version"])
    if not afni_check["available"]:
        # Fallback: check for '3dinfo' which is a core AFNI tool
        afni_check = check_tool_availability("afni", ["3dinfo", "-version"])
        if afni_check["available"]:
            afni_check["version"] = "Installed (version check via afni_version failed)"
        else:
            afni_check["available"] = False
            afni_check["error"] = "AFNI not found. Please ensure AFNI is installed and in PATH."
    results["AFNI"] = afni_check
    
    return results

def main():
    """
    Main entry point for the dependency check script.
    
    Checks for FSL and AFNI availability, prints results to stdout,
    and writes a JSON report to data/processed/dependency_check.json.
    
    Exits with code 1 if any required tool is missing, 0 otherwise.
    """
    print("Checking system dependencies for FSL and AFNI...")
    print("-" * 50)
    
    results = check_all_tools()
    
    all_available = True
    for tool, status in results.items():
        status_str = "✓ Available" if status["available"] else "✗ Missing"
        print(f"{tool}: {status_str}")
        
        if status["available"]:
            print(f"  Version: {status['version']}")
        else:
            print(f"  Error: {status['error']}")
            all_available = False
        
        print()
    
    # Ensure output directory exists
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "dependency_check.json"
    
    report = {
        "check_timestamp": None,  # Will be set by execution environment if needed, or left as null
        "dependencies": results,
        "all_available": all_available
    }
    
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Report written to: {output_file}")
    
    if not all_available:
        print("\nERROR: One or more required dependencies are missing.")
        print("Please install the missing tools and ensure they are in your PATH.")
        sys.exit(1)
    else:
        print("\nAll required dependencies are available.")
        sys.exit(0)

if __name__ == "__main__":
    main()