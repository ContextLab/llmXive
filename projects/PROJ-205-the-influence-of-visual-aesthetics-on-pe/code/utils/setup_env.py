import os
import sys
from pathlib import Path
from utils.config import ENV_VAR_NAME, DEFAULT_CONSENT_PATH, get_project_root

def verify_irb_env() -> bool:
    """
    Verifies that the IRB consent environment variable is set correctly
    and points to a valid file.

    Returns:
        bool: True if valid, False otherwise.
    """
    project_root = get_project_root()
    env_path = os.getenv(ENV_VAR_NAME)
    
    print(f"Checking IRB Consent Environment Configuration...")
    print(f"  Environment Variable: {ENV_VAR_NAME}")
    print(f"  Current Value: {env_path if env_path else '(Not Set)'}")
    print(f"  Default Path: {DEFAULT_CONSENT_PATH}")

    if not env_path:
        print(f"  ⚠️  Warning: {ENV_VAR_NAME} is not set. Using default path.")
        expected_path = project_root / DEFAULT_CONSENT_PATH
    else:
        if Path(env_path).is_absolute():
            expected_path = Path(env_path)
        else:
            expected_path = project_root / env_path

    if expected_path.exists():
        print(f"  ✅ Success: Consent file found at {expected_path}")
        return True
    else:
        print(f"  ❌ Error: Consent file NOT found at {expected_path}")
        print(f"     Please ensure the file exists or set {ENV_VAR_NAME} correctly.")
        return False

def main():
    """
    Entry point for running the environment verification script.
    """
    success = verify_irb_env()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
