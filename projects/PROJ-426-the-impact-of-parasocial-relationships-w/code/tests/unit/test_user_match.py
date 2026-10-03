"""
Unit tests for the user matching module.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import hashlib
import sys
import io

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.match.user_match import hash_username, perform_matching, load_and_validate_loneliness_data


class TestHashUsername:
    """Tests for the hash_username function."""

    def test_hash_username_deterministic(self):
        """Test that the same username always produces the same hash."""
        username = "test_user"
        hash1 = hash_username(username)
        hash2 = hash_username(username)
        assert hash1 == hash2

    def test_hash_username_unique(self):
        """Test that different usernames produce different hashes."""
        username1 = "user_one"
        username2 = "user_two"
        assert hash_username(username1) != hash_username(username2)

    def test_hash_username_sha256_format(self):
        """Test that the hash is a valid SHA-256 hex string."""
        username = "test_user"
        hash_value = hash_username(username)
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_hash_username_case_sensitive(self):
        """Test that username hashing is case-sensitive."""
        assert hash_username("User") != hash_username("user")

    def test_hash_username_invalid_input(self):
        """Test that invalid inputs raise ValueError."""
        with pytest.raises(ValueError):
            hash_username("")
        with pytest.raises(ValueError):
            hash_username(None)


class TestPerformMatching:
    """Tests for the perform_matching function."""

    def test_perform_matching_basic(self):
        """Test basic matching functionality."""
        # Create sample loneliness data
        loneliness_df = pd.DataFrame({
            'username': ['user1', 'user2', 'user3'],
            'loneliness_score': [10, 20, 30]
        })
        
        # Create sample Pushshift data
        pushshift_df = pd.DataFrame({
            'author_hash': [hash_username('user1'), hash_username('user2')]
        })
        
        # Perform matching
        result = perform_matching(loneliness_df, pushshift_df)
        
        # Verify results
        assert len(result) == 2
        assert 'user_id' in result.columns
        assert all(col in result.columns for col in ['loneliness_score'])

    def test_perform_matching_no_matches(self):
        """Test matching when there are no common users."""
        loneliness_df = pd.DataFrame({
            'username': ['user1', 'user2'],
            'loneliness_score': [10, 20]
        })
        
        pushshift_df = pd.DataFrame({
            'author_hash': [hash_username('user3'), hash_username('user4')]
        })
        
        result = perform_matching(loneliness_df, pushshift_df)
        
        assert len(result) == 0

    def test_perform_matching_empty_pushshift(self):
        """Test matching with empty Pushshift data."""
        loneliness_df = pd.DataFrame({
            'username': ['user1', 'user2'],
            'loneliness_score': [10, 20]
        })
        
        pushshift_df = pd.DataFrame(columns=['author_hash'])
        
        result = perform_matching(loneliness_df, pushshift_df)
        
        assert len(result) == 0

    def test_perform_matching_all_matched(self):
        """Test matching when all users are found in Pushshift."""
        loneliness_df = pd.DataFrame({
            'username': ['user1', 'user2'],
            'loneliness_score': [10, 20]
        })
        
        pushshift_df = pd.DataFrame({
            'author_hash': [hash_username('user1'), hash_username('user2')]
        })
        
        result = perform_matching(loneliness_df, pushshift_df)
        
        assert len(result) == 2


class TestLoadAndValidateLonelinessData:
    """Tests for the load_and_validate_loneliness_data function."""

    def test_load_and_validate_valid_file(self):
        """Test loading a valid Parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.parquet"
            df = pd.DataFrame({
                'username': ['user1', 'user2'],
                'score': [10, 20]
            })
            df.to_parquet(test_file)
            
            result = load_and_validate_loneliness_data(test_file)
            assert len(result) == 2
            assert 'username' in result.columns

    def test_load_and_validate_missing_file(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_and_validate_loneliness_data(Path("/nonexistent/file.parquet"))

    def test_load_and_validate_missing_fields(self):
        """Test loading a file with missing required fields raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.parquet"
            df = pd.DataFrame({
                'other_field': [1, 2, 3]
            })
            df.to_parquet(test_file)
            
            with pytest.raises(ValueError):
                load_and_validate_loneliness_data(test_file, required_fields=('username',))

    def test_load_and_validate_invalid_usernames(self):
        """Test that invalid usernames are dropped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.parquet"
            df = pd.DataFrame({
                'username': ['valid_user', '', None, 'another_valid'],
                'score': [10, 20, 30, 40]
            })
            df.to_parquet(test_file)
            
            result = load_and_validate_loneliness_data(test_file)
            assert len(result) == 2
            assert all(result['username'].notna())
            assert all(result['username'] != '')