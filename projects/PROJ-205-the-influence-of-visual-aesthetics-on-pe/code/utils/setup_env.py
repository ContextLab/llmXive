"""
Utility to verify and document the required environment variables for the project.
Specifically ensures the IRB Consent File path is configured correctly.
"""
import os
import sys
from pathlib import Path

# Import the config module to verify paths
# Adjust import path if running as script vs module
sys.path.insert(0, str(Path(__file__).parent))
from config import ENV_VAR_NAME, DEFAULT_CONSENT_PATH, get_project_root

def verify_irb_env():
    """
    Verifies that the IRB consent file path is correctly configured.
    Checks the environment variable and the default location.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    project_root = get_project_root()
    env_val = os.getenv(ENV_VAR_NAME)
    
    print(f"Checking IRB Consent Configuration...")
    print(f"  Project Root: {project_root}")
    print(f"  Environment Variable '{ENV_VAR_NAME}': {env_val if env_val else '(not set)'}")
    print(f"  Default Path: {project_root / DEFAULT_CONSENT_PATH}")
    
    # Determine the target path
    if env_val:
        target_path = Path(env_val)
        if not target_path.is_absolute():
            target_path = project_root / target_path
    else:
        target_path = project_root / DEFAULT_CONSENT_PATH
    
    if target_path.exists():
        print(f"  ✓ Consent file found at: {target_path}")
        return True
    else:
        print(f"  ✗ Consent file NOT found at: {target_path}")
        print(f"  Action Required: Please create the file or set {ENV_VAR_NAME}.")
        return False

def main():
    """
    Entry point for running the verification script.
    """
    success = verify_irb_env()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()