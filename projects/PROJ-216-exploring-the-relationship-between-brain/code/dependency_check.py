import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def run_command(command: List[str], timeout: int = 30) -> Tuple[bool, str]:
    """
    Executes a shell command and returns success status and output.
    
    Args:
        command: List of command arguments.
        timeout: Maximum time to wait for command execution.
        
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return False, f"Command not found: {command[0]}"
    except Exception as e:
        return False, str(e)

def check_tool_availability(tool_name: str, version_args: List[str]) -> Dict[str, Any]:
    """
    Checks if a specific tool is available and retrieves its version.
    
    Args:
        tool_name: Name of the tool (e.g., 'fsl', 'afni').
        version_args: Arguments to get version info (e.g., ['--version']).
        
    Returns:
        Dictionary with availability status and version info.
    """
    available, output = run_command([tool_name] + version_args)
    
    return {
        "tool": tool_name,
        "available": available,
        "version_output": output if available else None,
        "error": output if not available else None
    }

def check_all_tools() -> Dict[str, Any]:
    """
    Checks availability of all required neuroimaging tools (FSL, AFNI).
    
    Returns:
        Dictionary containing status for each tool and overall summary.
    """
    results = {}
    
    # Check FSL
    # FSL typically uses 'fslnum' or 'fslversion' to get version
    fsl_result = check_tool_availability("fsl", ["--version"])
    if not fsl_result["available"]:
        # Try alternative FSL version command
        fsl_result = check_tool_availability("fslnum", [])
    results["FSL"] = fsl_result
    
    # Check AFNI
    # AFNI uses 'afni -version'
    afni_result = check_tool_availability("afni", ["-version"])
    results["AFNI"] = afni_result
    
    # Overall summary
    all_available = all(r["available"] for r in results.values())
    
    return {
        "tools": results,
        "all_available": all_available,
        "missing_tools": [name for name, res in results.items() if not res["available"]]
    }

def main():
    """
    Main entry point for the dependency check script.
    Checks for FSL and AFNI availability and writes results to data/processed/dependency_check.json.
    """
    print("Starting dependency check for FSL and AFNI...")
    
    # Run checks
    check_results = check_all_tools()
    
    # Prepare output directory
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON
    output_file = output_dir / "dependency_check.json"
    with open(output_file, "w") as f:
        json.dump(check_results, f, indent=2)
    
    # Print summary to console
    print(f"\nDependency Check Results:")
    print(f"  FSL: {'Available' if check_results['tools']['FSL']['available'] else 'Not Found'}")
    if check_results['tools']['FSL']['available']:
        print(f"    Version: {check_results['tools']['FSL']['version_output']}")
    else:
        print(f"    Error: {check_results['tools']['FSL']['error']}")
        
    print(f"  AFNI: {'Available' if check_results['tools']['AFNI']['available'] else 'Not Found'}")
    if check_results['tools']['AFNI']['available']:
        print(f"    Version: {check_results['tools']['AFNI']['version_output']}")
    else:
        print(f"    Error: {check_results['tools']['AFNI']['error']}")
        
    print(f"\nOverall Status: {'All tools available' if check_results['all_available'] else 'Some tools missing'}")
    
    if not check_results['all_available']:
        print(f"Missing tools: {', '.join(check_results['missing_tools'])}")
        print(f"Results written to: {output_file}")
        sys.exit(1)
    else:
        print(f"Results written to: {output_file}")
        sys.exit(0)

if __name__ == "__main__":
    main()
