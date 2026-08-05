"""
T011a: Implement verification logic to validate IRB content against IRB_PROTOCOL_ID.

This script ensures that the consent text found in the configured file path
matches the expected content hash defined by the IRB_PROTOCOL_ID environment variable.
It prevents the use of outdated or unauthorized consent forms.
"""
import os
import sys
import hashlib
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_consent_file_path, ENV_VAR_NAME, DEFAULT_CONSENT_PATH
from utils.helpers import format_timestamp


def compute_content_hash(file_path: Path) -> str:
    """
    Computes a SHA-256 hash of the file contents.
    
    Args:
        file_path: Path to the consent text file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Consent file not found: {file_path}")
        
    hasher = hashlib.sha256()
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read in chunks to handle large files safely, though consent is small
        for chunk in iter(lambda: f.read(4096), ""):
            hasher.update(chunk.encode('utf-8'))
    
    return hasher.hexdigest()


def verify_irb_content() -> bool:
    """
    Validates the IRB consent file against the IRB_PROTOCOL_ID environment variable.
    
    This function:
    1. Reads the path to the consent file from configuration.
    2. Checks if the IRB_PROTOCOL_ID environment variable is set.
    3. Computes the SHA-256 hash of the consent file content.
    4. Compares the computed hash with the expected hash from the environment variable.
    
    Returns:
        True if validation passes.
        
    Raises:
        ValueError: If the environment variable is missing or the hashes do not match.
        FileNotFoundError: If the consent file is missing.
    """
    consent_path = get_consent_file_path()
    expected_hash = os.environ.get(ENV_VAR_NAME)
    
    if not expected_hash:
        raise ValueError(
            f"Critical Error: Environment variable '{ENV_VAR_NAME}' is not set. "
            "The system cannot verify the IRB protocol version without this identifier. "
            "Please set the IRB_PROTOCOL_ID in your environment."
        )
    
    # Normalize hashes (strip whitespace just in case)
    expected_hash = expected_hash.strip()
    
    print(f"[VERIFY] Checking consent file: {consent_path}")
    print(f"[VERIFY] Expected IRB Protocol ID (Hash): {expected_hash[:16]}...")
    
    actual_hash = compute_content_hash(consent_path)
    print(f"[VERIFY] Actual Content Hash:           {actual_hash[:16]}...")
    
    if actual_hash != expected_hash:
        raise ValueError(
            f"CRITICAL SECURITY FAILURE: Consent file content does not match "
            f"the approved IRB Protocol ID.\n"
            f"Expected: {expected_hash}\n"
            f"Found:    {actual_hash}\n"
            f"Path:     {consent_path}\n"
            f"\nThe survey cannot proceed. The consent text must be updated to match "
            f"the approved protocol or the environment variable must be corrected."
        )
    
    print(f"[VERIFY] SUCCESS: Consent file verified against IRB Protocol ID.")
    return True


def main():
    """
    Entry point for the verification script.
    """
    try:
        verify_irb_content()
        return 0
    except (ValueError, FileNotFoundError, PermissionError) as e:
        print(f"[ERROR] Verification failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[ERROR] Unexpected error during verification: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())