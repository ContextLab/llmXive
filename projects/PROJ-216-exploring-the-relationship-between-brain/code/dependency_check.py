"""
System-level dependency check script for FSL/AFNI availability.

This script verifies that the required neuroimaging tools (FSL and AFNI)
are installed and accessible in the system PATH before running the
preprocessing pipeline.

Usage:
    python code/dependency_check.py
    python code/dependency_check.py --verbose
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configuration
REQUIRED_TOOLS = {
    "fsl": {
        "command": "fsl",
        "version_flag": "--version",
        "min_version": None,  # Any version is acceptable
        "description": "FSL (FMRIB Software Library)"
    },
    "afni": {
        "command": "afni",
        "version_flag": "-ver",
        "min_version": None,
        "description": "AFNI (Analysis of Functional NeuroImages)"
    }
}

def run_command(command: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
    """
    Execute a shell command and capture stdout/stderr.
    
    Args:
        command: List of command arguments
        timeout: Maximum execution time in seconds
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return (
            result.returncode == 0,
            result.stdout.strip(),
            result.stderr.strip()
        )
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return False, "", "Command not found in PATH"
    except Exception as e:
        return False, "", f"Execution error: {str(e)}"

def check_tool_availability(tool_name: str) -> Dict[str, Any]:
    """
    Check if a specific tool is available and get its version.
    
    Args:
        tool_name: Name of the tool to check (e.g., 'fsl', 'afni')
        
    Returns:
        Dictionary with availability status and details
    """
    if tool_name not in REQUIRED_TOOLS:
        return {
            "available": False,
            "error": f"Unknown tool: {tool_name}"
        }
    
    tool_config = REQUIRED_TOOLS[tool_name]
    command = [tool_config["command"], tool_config["version_flag"]]
    
    success, stdout, stderr = run_command(command)
    
    return {
        "tool": tool_name,
        "description": tool_config["description"],
        "available": success,
        "version": stdout if success else None,
        "error": stderr if not success else None,
        "command_used": " ".join(command)
    }

def check_all_tools(verbose: bool = False) -> Dict[str, Any]:
    """
    Check availability of all required tools.
    
    Args:
        verbose: If True, print detailed output to stdout
        
    Returns:
        Dictionary with overall status and per-tool details
    """
    results = {}
    all_available = True
    
    for tool_name in REQUIRED_TOOLS:
        result = check_tool_availability(tool_name)
        results[tool_name] = result
        
        if not result["available"]:
            all_available = False
            
        if verbose:
            status = "✓" if result["available"] else "✗"
            print(f"{status} {result['description']} ({tool_name})")
            if result["available"]:
                print(f"  Version: {result['version']}")
            else:
                print(f"  Error: {result['error']}")
    
    return {
        "all_available": all_available,
        "timestamp": None,  # Will be set by main if needed
        "tools": results
    }

def main():
    """Main entry point for the dependency check script."""
    import argparse
    import datetime
    
    parser = argparse.ArgumentParser(
        description="Check system dependencies for FSL and AFNI"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Save results to a JSON file"
    )
    
    args = parser.parse_args()
    
    # Run checks
    results = check_all_tools(verbose=args.verbose)
    results["timestamp"] = datetime.datetime.now().isoformat()
    
    # Determine exit code
    exit_code = 0 if results["all_available"] else 1
    
    # Output handling
    if args.json or args.output:
        json_output = json.dumps(results, indent=2)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(json_output)
            print(f"Results saved to: {output_path}")
        else:
            print(json_output)
    elif args.verbose:
        print(f"\nOverall status: {'All dependencies available' if results['all_available'] else 'Missing dependencies'}")
    else:
        # Default minimal output
        if results["all_available"]:
            print("All required dependencies (FSL, AFNI) are available.")
        else:
            missing = [t for t, r in results["tools"].items() if not r["available"]]
            print(f"Missing dependencies: {', '.join(missing)}")
            print("Please install the required tools and ensure they are in your PATH.")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
