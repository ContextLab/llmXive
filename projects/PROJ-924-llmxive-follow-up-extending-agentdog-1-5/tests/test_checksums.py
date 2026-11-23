import json
import os
import tempfile
from pathlib import Path

import pytest

from code.data_loader import (
    LoudFailureError,
    compute_sha256,
    verify_checksum,
    validate_data_integrity,
)
from code.config import get_path

def test_compute_sha256():
    """Test that compute_sha256 returns a valid SHA256 hash."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum = compute_sha256(temp_path)
        assert len(checksum) == 64  # SHA256 hex string length
        assert all(c in "0123456789abcdef" for c in checksum)
    finally:
        os.unlink(temp_path)

def test_verify_checksum_success():
    """Test verify_checksum returns True for matching checksums."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum = compute_sha256(temp_path)
        result = verify_checksum(temp_path, checksum)
        assert result is True
    finally:
        os.unlink(temp_path)

def test_verify_checksum_failure():
    """Test verify_checksum raises LoudFailureError for mismatched checksums."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        with pytest.raises(LoudFailureError, match="Checksum mismatch"):
            verify_checksum(temp_path, "invalid_checksum")
    finally:
        os.unlink(temp_path)

def test_verify_checksum_file_not_found():
    """Test verify_checksum raises LoudFailureError for missing file."""
    with pytest.raises(LoudFailureError, match="File not found"):
        verify_checksum("/nonexistent/file.txt", "some_checksum")

def test_validate_data_integrity():
    """Test validate_data_integrity with valid checksums."""
    # Create temporary files
    temp_files = []
    for i in range(2):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=f"_file{i}.txt") as f:
            f.write(f"content {i}")
            temp_files.append(f.name)

    # Create checksums dictionary
    checksums = {}
    for file_path in temp_files:
        checksums[file_path] = compute_sha256(file_path)

    # Create temporary checksum file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump({"algorithm": "sha256", "files": checksums}, f)
        checksum_file = f.name

    try:
        results = validate_data_integrity(temp_files, checksum_file)
        assert all(results.values())
        assert len(results) == len(temp_files)
    finally:
        for file_path in temp_files:
            os.unlink(file_path)
        os.unlink(checksum_file)

def test_validate_data_integrity_missing_checksum():
    """Test validate_data_integrity raises error when checksum is missing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("content")
        temp_path = f.name

    try:
        checksums = {"/nonexistent/file.txt": "some_checksum"}
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"algorithm": "sha256", "files": checksums}, f)
            checksum_file = f.name

        try:
            with pytest.raises(LoudFailureError, match="No checksum registered"):
                validate_data_integrity([temp_path], checksum_file)
        finally:
            os.unlink(checksum_file)
    finally:
        os.unlink(temp_path)

def test_validate_data_integrity_mismatch():
    """Test validate_data_integrity raises error on checksum mismatch."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("content")
        temp_path = f.name

    try:
        checksums = {temp_path: "invalid_checksum"}
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            json.dump({"algorithm": "sha256", "files": checksums}, f)
            checksum_file = f.name

        try:
            with pytest.raises(LoudFailureError, match="Checksum mismatch"):
                validate_data_integrity([temp_path], checksum_file)
        finally:
            os.unlink(checksum_file)
    finally:
        os.unlink(temp_path)

def test_validate_data_integrity_missing_file():
    """Test validate_data_integrity raises error when file is missing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        json.dump({"algorithm": "sha256", "files": {"/nonexistent/file.txt": "checksum"}}, f)
        checksum_file = f.name

    try:
        with pytest.raises(LoudFailureError, match="File not found"):
            validate_data_integrity(["/nonexistent/file.txt"], checksum_file)
    finally:
        os.unlink(checksum_file)
