"""
Tests for the encryption module.
"""
import pytest
import sys
import os
import json
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.encryption import (
    encrypt_data,
    decrypt_data,
    encrypt_json_object,
    decrypt_json_object,
    encrypt_sensitive_fields,
    decrypt_sensitive_fields,
    get_encryption_key,
    derive_key_from_password
)

class TestEncryption:
    """Test cases for encryption functionality."""

    @patch.dict(os.environ, {'CODEX_ENCRYPTION_KEY': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'})
    def test_encrypt_decrypt_basic(self):
        """Test basic encryption and decryption."""
        key = get_encryption_key()
        original = "Sensitive data"
        
        encrypted = encrypt_data(original, key)
        decrypted = decrypt_data(encrypted, key)
        
        assert decrypted == original
        assert encrypted != original
        assert len(encrypted) > len(original)

    @patch.dict(os.environ, {'CODEX_ENCRYPTION_KEY': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'})
    def test_encrypt_decrypt_json(self):
        """Test JSON object encryption and decryption."""
        key = get_encryption_key()
        original = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30
        }
        
        encrypted = encrypt_json_object(original, key)
        decrypted = decrypt_json_object(encrypted, key)
        
        assert decrypted == original

    @patch.dict(os.environ, {'CODEX_ENCRYPTION_KEY': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'})
    def test_sensitive_field_encryption(self):
        """Test encryption of sensitive fields in a record."""
        key = get_encryption_key()
        record = {
            'id': 'P-123',
            'name': 'Alice',
            'email': 'alice@test.com',
            'age': 25
        }
        
        encrypted_record = encrypt_sensitive_fields(record, key)
        decrypted_record = decrypt_sensitive_fields(encrypted_record, key)
        
        # Non-sensitive fields should be preserved
        assert decrypted_record['id'] == 'P-123'
        assert decrypted_record['age'] == 25
        
        # Sensitive fields should be decrypted back
        assert decrypted_record['name'] == 'Alice'
        assert decrypted_record['email'] == 'alice@test.com'

    @patch.dict(os.environ, {'CODEX_ENCRYPTION_KEY': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'})
    def test_decrypt_invalid_key_raises(self):
        """Test that decryption with wrong key raises error."""
        key = get_encryption_key()
        wrong_key = b'B' * 32
        
        original = "Test data"
        encrypted = encrypt_data(original, key)
        
        with pytest.raises(ValueError):
            decrypt_data(encrypted, wrong_key)

    @patch.dict(os.environ, {'CODEX_ENCRYPTION_KEY': 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'})
    def test_decrypt_corrupted_data_raises(self):
        """Test that decryption with corrupted data raises error."""
        key = get_encryption_key()
        
        original = "Test data"
        encrypted = encrypt_data(original, key)
        
        # Corrupt the encrypted data
        corrupted = encrypted[:-5] + "XXXXX"
        
        with pytest.raises(ValueError):
            decrypt_data(corrupted, key)

    def test_derive_key_from_password(self):
        """Test key derivation from password."""
        password = "strong_password_123"
        key, salt = derive_key_from_password(password)
        
        assert len(key) == 32
        assert len(salt) == 32
        
        # Same password should produce same key with same salt
        key2, salt2 = derive_key_from_password(password, salt)
        assert key == key2

    def test_derive_key_different_salt(self):
        """Test that different salts produce different keys."""
        password = "test_password"
        
        key1, salt1 = derive_key_from_password(password)
        key2, salt2 = derive_key_from_password(password)
        
        assert salt1 != salt2
        assert key1 != key2

    @patch.dict(os.environ, {}, clear=True)
    def test_key_generation_when_missing(self):
        """Test that a key is generated when env var is missing."""
        # This should print instructions and return a new key
        with patch('sys.stderr') as mock_stderr:
            key = get_encryption_key()
            assert len(key) == 32

    def test_invalid_base64_key_raises(self):
        """Test that invalid base64 key raises error."""
        with patch.dict(os.environ, {'CODEX_ENCRYPTION_KEY': 'invalid-base64!!!'}):
            with pytest.raises(ValueError):
                get_encryption_key()

    def test_wrong_key_length_raises(self):
        """Test that key of wrong length raises error."""
        invalid_key = base64.b64encode(b'short').decode('utf-8')
        with patch.dict(os.environ, {'CODEX_ENCRYPTION_KEY': invalid_key}):
            with pytest.raises(ValueError):
                get_encryption_key()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
