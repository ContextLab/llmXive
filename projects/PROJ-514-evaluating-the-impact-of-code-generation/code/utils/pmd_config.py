"""
Configuration and utility functions for PMD static analysis integration.
Ensures PMD CLI availability and provides default rule set configurations.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

# Default PMD version if not specified in environment
DEFAULT_PMD_VERSION = "6.55.0"

# Default Java rulesets for the 4 target smell categories
# Long Method, Duplicated Code, Feature Envy, Long Parameter List
DEFAULT_RULESETS = [
    "rulesets/java/longmethod.xml",
    "rulesets/java/duplicatemethods.xml",
    "rulesets/java/featureenvy.xml",
    "rulesets/java/longparameterlist.xml"
]

def get_pmd_home() -> Optional[str]:
    """
    Retrieve the PMD_HOME environment variable or common installation paths.
    
    Returns:
        str: Path to PMD installation directory, or None if not found.
    """
    # Check environment variable first
    pmd_home = os.environ.get("PMD_HOME")
    if pmd_home and Path(pmd_home).exists():
        return pmd_home
    
    # Check common installation paths
    common_paths = [
        Path.home() / ".pmd" / f"pmd-bin-{DEFAULT_PMD_VERSION}",
        Path("/opt/pmd") / f"pmd-bin-{DEFAULT_PMD_VERSION}",
        Path("/usr/local/pmd") / f"pmd-bin-{DEFAULT_PMD_VERSION}"
    ]
    
    for path in common_paths:
        if path.exists():
            return str(path)
    
    return None

def check_pmd_availability() -> Tuple[bool, str]:
    """
    Check if PMD CLI is available in the system PATH.
    
    Returns:
        Tuple[bool, str]: (is_available, message)
    """
    try:
        result = subprocess.run(
            ["pmd", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, f"PMD is available: {result.stdout.strip()}"
        else:
            return False, f"PMD returned non-zero exit code: {result.stderr}"
    except FileNotFoundError:
        return False, "PMD command not found in PATH. Please install PMD or set PMD_HOME."
    except subprocess.TimeoutExpired:
        return False, "PMD version check timed out."
    except Exception as e:
        return False, f"Error checking PMD availability: {str(e)}"

def get_pmd_executable() -> Optional[str]:
    """
    Locate the PMD executable based on PMD_HOME or PATH.
    
    Returns:
        str: Path to PMD executable, or None if not found.
    """
    # Check PATH first
    pmd_path = subprocess.run(
        ["which", "pmd"],
        capture_output=True,
        text=True
    )
    if pmd_path.returncode == 0:
        return pmd_path.stdout.strip()
    
    # Check PMD_HOME
    pmd_home = get_pmd_home()
    if pmd_home:
        pmd_exec = Path(pmd_home) / "bin" / "pmd"
        if pmd_exec.exists():
            return str(pmd_exec)
    
    return None

def validate_pmd_rulesets(rulesets: list) -> Tuple[bool, list]:
    """
    Validate that specified PMD rulesets exist.
    
    Args:
        rulesets: List of ruleset paths to validate.
        
    Returns:
        Tuple[bool, list]: (all_valid, missing_rulesets)
    """
    missing = []
    pmd_home = get_pmd_home()
    
    if not pmd_home:
        return False, rulesets  # Can't validate without PMD installation
    
    ruleset_dir = Path(pmd_home) / "etc" / "rulesets" / "java"
    
    for ruleset in rulesets:
        # Extract the ruleset filename from the path
        ruleset_name = Path(ruleset).name
        ruleset_path = ruleset_dir / ruleset_name
        
        if not ruleset_path.exists():
            missing.append(ruleset)
    
    return len(missing) == 0, missing

def main():
    """
    Main entry point for PMD environment validation.
    Used for CI checks and local environment verification.
    """
    print("=== PMD Environment Validation ===")
    
    # Check PMD availability
    is_available, message = check_pmd_availability()
    print(f"PMD Availability: {message}")
    
    if not is_available:
        print("ERROR: PMD is not available. Please install PMD or configure PMD_HOME.")
        sys.exit(1)
    
    # Get executable path
    pmd_exec = get_pmd_executable()
    print(f"PMD Executable: {pmd_exec}")
    
    # Validate default rulesets
    all_valid, missing = validate_pmd_rulesets(DEFAULT_RULESETS)
    if all_valid:
        print(f"All default rulesets are available: {len(DEFAULT_RULESETS)} rulesets")
    else:
        print(f"WARNING: Missing rulesets: {missing}")
    
    print("=== Validation Complete ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())