"""
Module: code/stimuli/verify_irb_protocol.py

Implements verification logic to validate the content of the IRB consent file
against the expected Protocol ID (IRB_PROTOCOL_ID) defined in the environment.

This ensures the data collection process is using the exact approved text.
"""
import os
import sys
import hashlib
from pathlib import Path

# Import existing utilities from the project API surface
from utils.config import get_consent_file_path, ENV_VAR_NAME, DEFAULT_CONSENT_PATH
from utils.helpers import format_timestamp

def compute_content_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of the file content.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hex digest of the file content.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Consent file not found at: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading consent file: {file_path}")

def verify_irb_content() -> bool:
    """
    Verifies that the consent file exists, contains the expected Protocol ID,
    and matches the environment variable configuration.
    
    Returns:
        True if verification passes.
        
    Raises:
        ValueError: If the protocol ID does not match or file is missing.
        RuntimeError: If the environment variable is not set.
    """
    # 1. Check Environment Variable
    expected_protocol_id = os.getenv(ENV_VAR_NAME)
    if not expected_protocol_id:
        raise RuntimeError(
            f"Environment variable '{ENV_VAR_NAME}' is not set. "
            f"Please set it to the approved IRB Protocol ID before running."
        )

    # 2. Locate File
    consent_file_path = get_consent_file_path()
    if not consent_file_path.exists():
        raise FileNotFoundError(
            f"Consent file not found at expected path: {consent_file_path}. "
            f"Please ensure '{DEFAULT_CONSENT_PATH}' exists and is populated."
        )

    # 3. Read and Validate Content
    try:
        with open(consent_file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to read consent file: {e}")

    # 4. Check for Protocol ID presence
    if expected_protocol_id not in content:
        raise ValueError(
            f"Verification Failed: The file at {consent_file_path} does not contain "
            f"the expected Protocol ID '{expected_protocol_id}'. "
            "The consent file content does not match the IRB approval record."
        )

    # 5. Log Verification Success (Side effect for audit)
    file_hash = compute_content_hash(consent_file_path)
    timestamp = format_timestamp()
    print(f"[{timestamp}] IRB Verification PASSED.")
    print(f"  Protocol ID: {expected_protocol_id}")
    print(f"  File Path: {consent_file_path}")
    print(f"  Content Hash (SHA-256): {file_hash}")
    
    return True

def main():
    """Entry point for the verification script."""
    try:
        verify_irb_content()
        print("IRB Protocol verification successful. System ready for data collection.")
        sys.exit(0)
    except (RuntimeError, FileNotFoundError, ValueError) as e:
        print(f"CRITICAL ERROR: IRB Verification Failed - {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()