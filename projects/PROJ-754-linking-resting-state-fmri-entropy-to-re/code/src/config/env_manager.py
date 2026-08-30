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
    Assumes the project root is two levels up from this file:
    code/src/config/env_manager.py -> code/ -> project root
    """
    current_file = Path(__file__).resolve()
    # Navigate up from code/src/config to code
    code_dir = current_file.parent.parent.parent
    # If we are in code/, that is the root relative to the repo structure described
    # However, usually 'code' is a subfolder in the repo, or the repo IS the code folder.
    # Based on T001, the root has src/, data/, etc.
    # The file is at code/src/config/env_manager.py.
    # If the repo root is 'code', then parent.parent is 'code'.
    # If the repo root is parent of 'code', then parent.parent.parent is repo root.
    # Let's assume the standard layout where 'code' is the root of the project artifacts
    # or we look for 'src' in the parent.
    
    # Strategy: Look upwards for a directory containing 'src' and 'data'
    candidate = code_dir
    while candidate.parent != candidate:
        if (candidate / "src").exists() and (candidate / "data").exists():
            return candidate
        candidate = candidate.parent
    
    # Fallback: if not found, assume the immediate parent of 'code' is root, 
    # or just return 'code' if it looks like a root.
    if (code_dir / "src").exists():
        return code_dir
    return code_dir.parent

def get_hcp_token() -> str:
    """
    Retrieve the HCP_TOKEN from environment variables.
    
    Returns:
        str: The token value.
        
    Raises:
        ValueError: If HCP_TOKEN is missing or empty.
    """
    token = os.getenv("HCP_TOKEN")
    if not token or token.strip() == "":
        raise ValueError("HCP_TOKEN is required but not found in environment variables.")
    return token.strip()

def validate_hcp_credentials() -> bool:
    """
    Validate that HCP credentials are present and non-empty.
    
    Returns:
        bool: True if valid.
        
    Raises:
        ValueError: If credentials are missing.
    """
    try:
        token = get_hcp_token()
        # Basic validation: token must be non-empty string
        if len(token) < 8:
            # Heuristic: HCP tokens are usually long strings
            raise ValueError("HCP_TOKEN appears too short to be valid.")
        return True
    except ValueError as e:
        raise e

def get_optional_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve an optional environment variable.
    
    Args:
        var_name: Name of the environment variable.
        default: Default value if not found.
        
    Returns:
        The value or the default.
    """
    return os.getenv(var_name, default)

def check_environment() -> dict:
    """
    Check the status of all required environment variables.
    
    Returns:
        dict: Status of checks.
    """
    status = {
        "HCP_TOKEN": False,
        "valid": True,
        "errors": []
    }
    
    try:
        get_hcp_token()
        status["HCP_TOKEN"] = True
    except ValueError as e:
        status["valid"] = False
        status["errors"].append(str(e))
        
    return status

def main():
    """Main entry point for CLI execution."""
    print("Checking environment configuration...")
    status = check_environment()
    
    if status["valid"]:
        print("✓ Environment check passed.")
        print(f"  HCP_TOKEN: {'Present' if status['HCP_TOKEN'] else 'Missing'}")
        return 0
    else:
        print("✗ Environment check failed.")
        for err in status["errors"]:
            print(f"  - {err}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
