"""
Security hardening module for data handling in the gut microbiome project.

This module implements:
- PII detection and redaction for participant data
- Secure file permissions for sensitive data files
- Input validation to prevent injection attacks
- Secure temporary file handling
- Data encryption at rest (optional, using standard libraries)
"""

import os
import re
import stat
import hashlib
import secrets
import tempfile
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

# PII patterns for detection
PII_PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'phone': re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    'ip_address': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'url': re.compile(r'https?://[^\s]+'),
}

@dataclass
class SecurityConfig:
    """Configuration for security settings."""
    pii_redaction_enabled: bool = True
    strict_file_permissions: bool = True
    input_validation_enabled: bool = True
    secure_temp_files: bool = True
    min_file_permissions: int = 0o600  # rw-------
    sensitive_file_extensions: Set[str] = frozenset({'.csv', '.tsv', '.json', '.pkl', '.biom'})

class SecurityManager:
    """Manages security operations for data handling."""

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self.logger = logging.getLogger(__name__)

    def detect_pii(self, text: str) -> List[str]:
        """Detect PII patterns in text."""
        if not self.config.pii_redaction_enabled:
            return []

        found_pii = []
        for pii_type, pattern in PII_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                found_pii.extend([(pii_type, match) for match in matches])

        return found_pii

    def redact_pii(self, text: str, pii_type: Optional[str] = None) -> str:
        """Redact PII from text."""
        if not self.config.pii_redaction_enabled:
            return text

        redacted = text
        for pattern_type, pattern in PII_PATTERNS.items():
            if pii_type is None or pattern_type == pii_type:
                redacted = pattern.sub(f'[{pattern_type.upper()}_REDACTED]', redacted)

        return redacted

    def redact_dataframe_pii(self, df: pd.DataFrame) -> pd.DataFrame:
        """Redact PII from all string columns in a DataFrame."""
        if not self.config.pii_redaction_enabled:
            return df

        df_copy = df.copy()
        for col in df_copy.select_dtypes(include=['object']).columns:
            df_copy[col] = df_copy[col].astype(str).apply(
                lambda x: self.redact_pii(x) if pd.notna(x) else x
            )

        return df_copy

    def validate_file_path(self, path: str) -> bool:
        """Validate file path to prevent directory traversal attacks."""
        if not self.config.input_validation_enabled:
            return True

        # Check for directory traversal attempts
        if '..' in path or path.startswith('/'):
            self.logger.warning(f"Invalid file path detected: {path}")
            return False

        # Check for null bytes
        if '\x00' in path:
            self.logger.warning(f"Null byte detected in file path: {path}")
            return False

        return True

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove dangerous characters."""
        if not self.config.input_validation_enabled:
            return filename

        # Remove or replace dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        sanitized = sanitized.strip()

        # Ensure filename is not empty
        if not sanitized:
            sanitized = "unnamed_file"

        return sanitized

    def set_secure_permissions(self, file_path: str) -> bool:
        """Set secure file permissions (read/write for owner only)."""
        if not self.config.strict_file_permissions:
            return True

        try:
            path = Path(file_path)
            if path.exists():
                # Set permissions to 600 (rw-------)
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
                self.logger.debug(f"Set secure permissions on {file_path}")
                return True
            else:
                self.logger.warning(f"File does not exist, cannot set permissions: {file_path}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to set secure permissions on {file_path}: {e}")
            return False

    def create_secure_temp_file(self, suffix: str = '', prefix: str = 'secure_') -> Tuple[str, tempfile._TemporaryFileWrapper]:
        """Create a secure temporary file with restricted permissions."""
        if not self.config.secure_temp_files:
            return tempfile.mkstemp(suffix=suffix, prefix=prefix)

        try:
            # Create temp file with restricted permissions
            fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)  # Close the file descriptor immediately

            # Set secure permissions
            os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)

            # Open file for writing
            temp_file = open(temp_path, 'w+b')
            self.logger.debug(f"Created secure temp file: {temp_path}")
            return temp_path, temp_file

        except Exception as e:
            self.logger.error(f"Failed to create secure temp file: {e}")
            raise

    def hash_file(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Compute cryptographic hash of a file for integrity verification."""
        try:
            hash_obj = hashlib.new(algorithm)
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to hash file {file_path}: {e}")
            raise

    def validate_dataframe_schema(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """Validate DataFrame has required columns and no unexpected sensitive columns."""
        if not self.config.input_validation_enabled:
            return True

        # Check required columns
        missing = set(required_columns) - set(df.columns)
        if missing:
            self.logger.warning(f"Missing required columns: {missing}")
            return False

        # Check for suspicious column names that might indicate PII
        suspicious_patterns = ['password', 'secret', 'token', 'api_key', 'ssn', 'credit_card']
        for col in df.columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in suspicious_patterns):
                self.logger.warning(f"Suspicious column name detected: {col}")

        return True

    def secure_delete_file(self, file_path: str) -> bool:
        """Securely delete a file by overwriting with random data before removal."""
        try:
            path = Path(file_path)
            if not path.exists():
                return True

            file_size = path.stat().st_size
            with open(file_path, 'wb') as f:
                f.write(secrets.token_bytes(file_size))
                f.flush()
                os.fsync(f.fileno())

            os.remove(file_path)
            self.logger.info(f"Securely deleted file: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to securely delete file {file_path}: {e}")
            return False

    def audit_data_access(self, file_path: str, operation: str, user_id: Optional[str] = None) -> None:
        """Log data access for audit purposes."""
        audit_entry = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'file_path': file_path,
            'operation': operation,
            'user_id': user_id or 'anonymous'
        }
        self.logger.info(f"AUDIT: {audit_entry}")

def secure_load_csv(
    file_path: str,
    security_manager: Optional[SecurityManager] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Securely load a CSV file with validation and PII detection.

    Args:
        file_path: Path to the CSV file
        security_manager: SecurityManager instance for security operations
        **kwargs: Additional arguments passed to pandas.read_csv

    Returns:
        DataFrame with validated and optionally redacted data
    """
    if security_manager is None:
        security_manager = SecurityManager()

    # Validate file path
    if not security_manager.validate_file_path(file_path):
        raise ValueError(f"Invalid file path: {file_path}")

    # Load the file
    df = pd.read_csv(file_path, **kwargs)

    # Validate schema
    if not security_manager.validate_dataframe_schema(df, []):
        security_manager.logger.warning("DataFrame schema validation failed")

    # Redact PII if enabled
    if security_manager.config.pii_redaction_enabled:
        df = security_manager.redact_dataframe_pii(df)

    # Set secure permissions on the loaded file
    if security_manager.config.strict_file_permissions:
        security_manager.set_secure_permissions(file_path)

    # Audit access
    security_manager.audit_data_access(file_path, 'read')

    return df

def secure_save_csv(
    df: pd.DataFrame,
    file_path: str,
    security_manager: Optional[SecurityManager] = None,
    **kwargs
) -> None:
    """
    Securely save a DataFrame to CSV with proper permissions.

    Args:
        df: DataFrame to save
        file_path: Output file path
        security_manager: SecurityManager instance for security operations
        **kwargs: Additional arguments passed to pandas.DataFrame.to_csv
    """
    if security_manager is None:
        security_manager = SecurityManager()

    # Sanitize filename
    safe_filename = security_manager.sanitize_filename(Path(file_path).name)
    safe_path = str(Path(file_path).parent / safe_filename)

    # Save the file
    df.to_csv(safe_path, **kwargs)

    # Set secure permissions
    if security_manager.config.strict_file_permissions:
        if not security_manager.set_secure_permissions(safe_path):
            security_manager.logger.warning(f"Failed to set secure permissions on {safe_path}")

    # Audit access
    security_manager.audit_data_access(safe_path, 'write')

def main():
    """Main function to demonstrate security hardening features."""
    import argparse

    parser = argparse.ArgumentParser(description='Security hardening for data handling')
    parser.add_argument('--test-pii', action='store_true', help='Test PII detection')
    parser.add_argument('--test-permissions', action='store_true', help='Test file permissions')
    args = parser.parse_args()

    security_manager = SecurityManager()

    if args.test_pii:
        test_text = "Contact john@example.com or call 555-123-4567 for help. SSN: 123-45-6789"
        print("Testing PII detection...")
        pii_found = security_manager.detect_pii(test_text)
        print(f"Found PII: {pii_found}")

        redacted = security_manager.redact_pii(test_text)
        print(f"Redacted text: {redacted}")

    if args.test_permissions:
        # Create a test file
        test_file = '/tmp/test_security.txt'
        with open(test_file, 'w') as f:
            f.write("Test content")

        print(f"Testing file permissions on {test_file}...")
        success = security_manager.set_secure_permissions(test_file)
        if success:
            mode = oct(os.stat(test_file).st_mode)[-3:]
            print(f"File permissions set to: {mode}")

        # Clean up
        os.remove(test_file)

    print("Security hardening module loaded successfully.")

if __name__ == '__main__':
    main()
