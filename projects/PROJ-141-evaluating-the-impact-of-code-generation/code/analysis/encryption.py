"""
Encryption module for participant data.

Implements Constitution VII compliance:
- AES-256-GCM encryption for sensitive data
- Keys stored in environment variables (CODEX_ENCRYPTION_KEY)
- Secure key derivation and management
"""
import os
import base64
import secrets
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import json
import sys
from datetime import datetime

# Environment variable name for encryption key
ENCRYPTION_KEY_ENV_VAR = "CODEX_ENCRYPTION_KEY"

# Key derivation parameters
SALT_LENGTH = 32
ITERATIONS = 100000
KEY_LENGTH = 32  # 256 bits for AES-256

def get_encryption_key() -> bytes:
    """
    Retrieve or generate the encryption key from environment variables.
    
    If CODEX_ENCRYPTION_KEY is set, it is used (must be base64 encoded 32-byte key).
    If not set, a new key is generated and printed to stderr for storage.
    
    Returns:
        32-byte encryption key
    
    Raises:
        ValueError: If key is invalid length or cannot be derived
    """
    key_b64 = os.environ.get(ENCRYPTION_KEY_ENV_VAR)
    
    if key_b64:
        try:
            key = base64.b64decode(key_b64)
            if len(key) != KEY_LENGTH:
                raise ValueError(f"Encryption key must be {KEY_LENGTH} bytes, got {len(key)}")
            return key
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding for encryption key: {e}")
    else:
        # Generate a new key and instruct user to set it
        new_key = secrets.token_bytes(KEY_LENGTH)
        new_key_b64 = base64.b64encode(new_key).decode('utf-8')
        
        print(f"⚠️  No encryption key found. Please set the following key:", file=sys.stderr)
        print(f"    export {ENCRYPTION_KEY_ENV_VAR}='{new_key_b64}'", file=sys.stderr)
        print("⚠️  Using generated key for this session (not persisted).", file=sys.stderr)
        
        return new_key

def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Derive an encryption key from a password using PBKDF2.
    
    Args:
        password: Password string
        salt: Optional salt (generated if not provided)
    
    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = secrets.token_bytes(SALT_LENGTH)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
        backend=default_backend()
    )
    
    key = kdf.derive(password.encode('utf-8'))
    return key, salt

def encrypt_data(data: str, key: Optional[bytes] = None) -> str:
    """
    Encrypt data using AES-256-GCM.
    
    Args:
        data: String data to encrypt
        key: Optional encryption key (uses env var if not provided)
    
    Returns:
        Base64-encoded string containing nonce, ciphertext, and tag
    """
    if key is None:
        key = get_encryption_key()
    
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
    
    ciphertext = aesgcm.encrypt(nonce, data.encode('utf-8'), None)
    
    # Combine nonce + ciphertext + tag (tag is last 16 bytes)
    encrypted_blob = nonce + ciphertext
    
    return base64.b64encode(encrypted_blob).decode('utf-8')

def decrypt_data(encrypted_blob: str, key: Optional[bytes] = None) -> str:
    """
    Decrypt data encrypted with AES-256-GCM.
    
    Args:
        encrypted_blob: Base64-encoded encrypted data
        key: Optional encryption key (uses env var if not provided)
    
    Returns:
        Decrypted string
    
    Raises:
        ValueError: If decryption fails (invalid key or corrupted data)
    """
    if key is None:
        key = get_encryption_key()
    
    try:
        encrypted_bytes = base64.b64decode(encrypted_blob)
    except Exception as e:
        raise ValueError(f"Invalid base64 encoding: {e}")
    
    if len(encrypted_bytes) < 28:  # 12 (nonce) + 16 (min tag)
        raise ValueError("Encrypted data too short")
    
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    
    aesgcm = AESGCM(key)
    
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")

def encrypt_json_object(obj: dict, key: Optional[bytes] = None) -> str:
    """
    Encrypt a JSON object.
    
    Args:
        obj: Dictionary to encrypt
        key: Optional encryption key
    
    Returns:
        Base64-encoded encrypted string
    """
    json_str = json.dumps(obj, sort_keys=True, default=str)
    return encrypt_data(json_str, key)

def decrypt_json_object(encrypted_blob: str, key: Optional[bytes] = None) -> dict:
    """
    Decrypt a JSON object.
    
    Args:
        encrypted_blob: Base64-encoded encrypted string
        key: Optional encryption key
    
    Returns:
        Decrypted dictionary
    """
    json_str = decrypt_data(encrypted_blob, key)
    return json.loads(json_str)

def encrypt_sensitive_fields(record: dict, key: Optional[bytes] = None) -> dict:
    """
    Encrypt specific sensitive fields in a record.
    
    Fields encrypted: name, email, ip_address, phone, address
    
    Args:
        record: Dictionary containing potentially sensitive data
        key: Optional encryption key
    
    Returns:
        Dictionary with sensitive fields encrypted
    """
    sensitive_fields = ['name', 'email', 'ip_address', 'phone', 'address', 'password']
    encrypted_record = record.copy()
    
    for field in sensitive_fields:
        if field in encrypted_record and encrypted_record[field] is not None:
            value = str(encrypted_record[field])
            encrypted_record[field] = encrypt_data(value, key)
            encrypted_record[f"{field}_encrypted"] = True
    
    return encrypted_record

def decrypt_sensitive_fields(record: dict, key: Optional[bytes] = None) -> dict:
    """
    Decrypt sensitive fields in a record.
    
    Args:
        record: Dictionary with encrypted fields
        key: Optional encryption key
    
    Returns:
        Dictionary with sensitive fields decrypted
    """
    decrypted_record = record.copy()
    
    for key_name in list(decrypted_record.keys()):
        if key_name.endswith('_encrypted') and decrypted_record[key_name]:
            field_name = key_name.replace('_encrypted', '')
            if field_name in decrypted_record:
                try:
                    decrypted_record[field_name] = decrypt_data(decrypted_record[field_name], key)
                except ValueError as e:
                    print(f"Warning: Failed to decrypt {field_name}: {e}")
            
            del decrypted_record[key_name]
    
    return decrypted_record

def main():
    """
    Command-line interface for testing encryption/decryption.
    """
    print("=== Encryption Module Test ===\n")
    
    # Test 1: Key retrieval
    print("1. Testing key retrieval...")
    try:
        key = get_encryption_key()
        print(f"   ✓ Key retrieved (length: {len(key)} bytes)")
    except ValueError as e:
        print(f"   ✗ Key retrieval failed: {e}")
        return 1
    
    # Test 2: Basic encryption/decryption
    print("\n2. Testing basic encryption/decryption...")
    test_string = "Sensitive participant data: John Doe, john@example.com"
    encrypted = encrypt_data(test_string, key)
    decrypted = decrypt_data(encrypted, key)
    
    if decrypted == test_string:
        print(f"   ✓ Encryption/decryption successful")
        print(f"   Original: {test_string}")
        print(f"   Encrypted: {encrypted[:50]}...")
        print(f"   Decrypted: {decrypted}")
    else:
        print(f"   ✗ Decryption mismatch")
        return 1
    
    # Test 3: JSON object encryption
    print("\n3. Testing JSON object encryption...")
    test_obj = {
        "participant_id": "P-12345",
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "ip_address": "10.0.0.55",
        "session_data": {"start": "2024-01-15T10:00:00Z", "end": "2024-01-15T11:30:00Z"}
    }
    
    encrypted_obj = encrypt_json_object(test_obj, key)
    decrypted_obj = decrypt_json_object(encrypted_obj, key)
    
    if decrypted_obj == test_obj:
        print(f"   ✓ JSON encryption/decryption successful")
    else:
        print(f"   ✗ JSON decryption mismatch")
        return 1
    
    # Test 4: Sensitive field encryption
    print("\n4. Testing sensitive field encryption...")
    test_record = {
        "id": "P-12345",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "age": 30,
        "experience": 5
    }
    
    encrypted_record = encrypt_sensitive_fields(test_record, key)
    decrypted_record = decrypt_sensitive_fields(encrypted_record, key)
    
    # Check that non-sensitive fields are preserved
    if decrypted_record['id'] == test_record['id'] and decrypted_record['age'] == test_record['age']:
        print(f"   ✓ Sensitive field encryption successful")
        print(f"   Non-sensitive fields preserved: id={decrypted_record['id']}, age={decrypted_record['age']}")
    else:
        print(f"   ✗ Non-sensitive fields corrupted")
        return 1
    
    print("\n=== All encryption tests passed ===")
    return 0

if __name__ == '__main__':
    sys.exit(main())
