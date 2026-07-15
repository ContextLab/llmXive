"""
Environment variable management for the project.
Handles HCP_TOKEN validation and project root detection.
"""
import os
import sys
from pathlib import Path
from typing import Optional

class EnvironmentError(Exception):
    """Custom exception for environment configuration errors."""
    pass

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from within the 'code' directory or its subdirectories.
    """
    # Try to find the root by looking for the 'data' directory relative to this file
    current_file = Path(__file__).resolve()
    # Standard structure: code/config/env_manager.py -> root is parent of code
    potential_root = current_file.parent.parent
    
    if (potential_root / "data").exists() and (potential_root / "code").exists():
        return potential_root
    
    # Fallback: check if we are in a standard repo structure
    if (current_file.parent.parent.parent / "data").exists():
        return current_file.parent.parent.parent
        
    raise EnvironmentError("Could not determine project root. Ensure 'data' and 'code' directories exist.")

def get_hcp_token() -> str:
    """
    Retrieve and validate the HCP_TOKEN environment variable.
    
    Returns:
        str: The token string.
        
    Raises:
        EnvironmentError: If the token is missing or empty.
    """
    token = os.getenv("HCP_TOKEN")
    if not token or not token.strip():
        raise EnvironmentError(
            "HCP_TOKEN environment variable is not set or is empty. "
            "Please set it to your HCP access token."
        )
    return token.strip()

def validate_hcp_credentials() -> bool:
    """
    Validate that HCP credentials are present and non-empty.
    
    Returns:
        bool: True if valid, raises EnvironmentError otherwise.
    """
    try:
        get_hcp_token()
        return True
    except EnvironmentError:
        raise

def get_optional_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve an optional environment variable without raising an error if missing.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if not found.
        
    Returns:
        Optional[str]: The value or the default.
    """
    return os.getenv(var_name, default)

def check_environment() -> dict:
    """
    Perform a comprehensive check of the environment.
    
    Returns:
        dict: Status of checks.
    """
    results = {
        "project_root": None,
        "hcp_token_valid": False,
        "errors": []
    }
    
    try:
        root = get_project_root()
        results["project_root"] = str(root)
    except EnvironmentError as e:
        results["errors"].append(str(e))
        
    try:
        validate_hcp_credentials()
        results["hcp_token_valid"] = True
    except EnvironmentError as e:
        results["errors"].append(f"HCP Token: {e}")
        
    return results

def main():
    """CLI entry point for environment checks."""
    print("Checking environment configuration...")
    results = check_environment()
    
    if results["project_root"]:
        print(f"✓ Project root detected: {results['project_root']}")
    else:
        print(f"✗ Project root error: {results['errors']}")
        
    if results["hcp_token_valid"]:
        print("✓ HCP_TOKEN is configured.")
    else:
        print("✗ HCP_TOKEN is missing or invalid.")
        
    if results["errors"]:
        print("\nErrors encountered:")
        for err in results["errors"]:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nEnvironment check passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
