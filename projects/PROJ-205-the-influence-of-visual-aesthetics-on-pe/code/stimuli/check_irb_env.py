import os
import sys
from pathlib import Path

from utils.config import get_consent_file_path, ENV_VAR_NAME, DEFAULT_CONSENT_PATH
from utils.helpers import generate_user_id

def verify_irb_content():
    """
    Validates that the IRB consent file exists and contains the required IRB_PROTOCOL_ID.
    
    Returns:
        tuple: (is_valid: bool, message: str)
    """
    # 1. Check if the environment variable is set
    protocol_id = os.getenv(ENV_VAR_NAME)
    if not protocol_id:
        return False, f"Environment variable '{ENV_VAR_NAME}' is not set."

    # 2. Resolve the consent file path
    try:
        consent_path = get_consent_file_path()
    except Exception as e:
        return False, f"Failed to resolve consent file path: {str(e)}"

    if not consent_path.exists():
        return False, f"Consent file not found at: {consent_path}"

    # 3. Read and validate content
    try:
        content = consent_path.read_text(encoding='utf-8')
    except Exception as e:
        return False, f"Failed to read consent file: {str(e)}"

    if not content.strip():
        return False, "Consent file is empty."

    # 4. Verify the protocol ID is present in the text
    if protocol_id not in content:
        return False, (
            f"IRB_PROTOCOL_ID '{protocol_id}' not found in the consent file content. "
            f"File path: {consent_path}"
        )

    return True, f"IRB verification successful. Protocol ID '{protocol_id}' found in {consent_path}."

def main():
    """
    Entry point for the IRB verification script.
    Exits with code 0 on success, 1 on failure.
    """
    is_valid, message = verify_irb_content()
    print(message)
    
    if is_valid:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
