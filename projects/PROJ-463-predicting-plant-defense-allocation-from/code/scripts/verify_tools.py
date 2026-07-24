import subprocess
import sys
from typing import Dict, Tuple

def check_tool(tool_name: str) -> Tuple[bool, str]:
    """
    Checks if a specific tool is installed and available in the system PATH.
    
    Args:
        tool_name: The name of the tool to check (e.g., 'fastp', 'hisat2', 'featureCounts').
    
    Returns:
        A tuple (is_installed, version_output).
        If installed, is_installed is True and version_output contains the version string.
        If not installed, is_installed is False and version_output contains the error message.
    """
    try:
        # Attempt to run the tool with a version flag to verify existence and get version
        # We use check_output to capture stdout, stderr is captured in the exception if it fails
        result = subprocess.run(
            [tool_name, '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Some tools output version to stderr (like featureCounts sometimes)
            output = result.stdout.strip() or result.stderr.strip()
            return True, output
        else:
            return False, f"Command returned non-zero: {result.stderr}"
    
    except FileNotFoundError:
        return False, f"Tool '{tool_name}' not found in PATH"
    except subprocess.TimeoutExpired:
        return False, f"Timeout while checking '{tool_name}'"
    except Exception as e:
        return False, f"Error checking '{tool_name}': {str(e)}"

def main():
    """
    Main entry point to verify installation of HISAT2, fastp, and featureCounts.
    """
    tools = ['fastp', 'hisat2', 'featureCounts']
    all_passed = True

    print("Verifying required bioinformatics tools...")
    print("-" * 50)

    for tool in tools:
        installed, output = check_tool(tool)
        status = "OK" if installed else "MISSING"
        print(f"{tool:15} : {status}")
        if installed:
            # Print first line of version output
            first_line = output.split('\n')[0]
            print(f"{'':15}   -> {first_line}")
        else:
            print(f"{'':15}   -> Error: {output}")
            all_passed = False
        print("-" * 50)

    if all_passed:
        print("SUCCESS: All required tools are installed and accessible.")
        sys.exit(0)
    else:
        print("FAILURE: One or more required tools are missing or not in PATH.")
        print("Please run the installation script: scripts/install_tools.sh")
        sys.exit(1)

if __name__ == "__main__":
    main()
