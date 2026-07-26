import subprocess
import sys
import json
import os
from pathlib import Path
from typing import Dict, Tuple, Optional

def check_tool(tool_name: str, version_flag: str = "--version") -> Tuple[bool, str, str]:
    """
    Check if a system tool is installed and executable.
    
    Args:
        tool_name: Name of the tool to check (e.g., 'fastp', 'hisat2', 'featureCounts')
        version_flag: Flag to get version info (default: "--version")
        
    Returns:
        Tuple of (is_installed, version_output, error_message)
    """
    try:
        result = subprocess.run(
            [tool_name, version_flag],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Extract version from output (usually first line)
            version_info = result.stdout.strip().split('\n')[0]
            return True, version_info, ""
        else:
            return False, "", result.stderr.strip()
            
    except FileNotFoundError:
        return False, "", f"Command '{tool_name}' not found in PATH"
    except subprocess.TimeoutExpired:
        return False, "", f"Command '{tool_name}' timed out"
    except Exception as e:
        return False, "", f"Error executing '{tool_name}': {str(e)}"

def main():
    """
    Main function to validate all required system tools and save results to manifest.
    """
    # Define required tools and their version flags
    tools_to_check = {
        "fastp": "--version",
        "hisat2": "--version",
        "featureCounts": "--version"
    }
    
    results = {
        "timestamp": "",
        "tools": {},
        "summary": {
            "total": len(tools_to_check),
            "passed": 0,
            "failed": 0
        }
    }
    
    # Get current timestamp
    from datetime import datetime
    results["timestamp"] = datetime.now().isoformat()
    
    print("Environment Validation Script")
    print("=" * 50)
    
    all_passed = True
    
    for tool_name, version_flag in tools_to_check.items():
        print(f"\nChecking {tool_name}...")
        is_installed, version_info, error_msg = check_tool(tool_name, version_flag)
        
        tool_result = {
            "installed": is_installed,
            "version": version_info if is_installed else None,
            "error": error_msg if not is_installed else None
        }
        
        results["tools"][tool_name] = tool_result
        
        if is_installed:
            print(f"  ✓ {tool_name} found: {version_info}")
            results["summary"]["passed"] += 1
        else:
            print(f"  ✗ {tool_name} NOT found: {error_msg}")
            all_passed = False
            results["summary"]["failed"] += 1
    
    print("\n" + "=" * 50)
    print(f"Summary: {results['summary']['passed']}/{results['summary']['total']} tools passed")
    
    # Ensure output directory exists
    output_dir = Path("data/manifests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write manifest
    output_file = output_dir / "env_validation.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nManifest saved to: {output_file}")
    
    if not all_passed:
        print("\nWARNING: Some tools are missing. Please install them before proceeding.")
        sys.exit(1)
    else:
        print("\nAll required tools are installed and ready.")
        sys.exit(0)

if __name__ == "__main__":
    main()
