import os
import tempfile
import pytest
from pathlib import Path

# Import the functions to test
# Note: We need to ensure the path is set correctly for imports if running from tests/
# Assuming standard project structure where code/ is at root
import sys
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "code"))

from checksum_utils import compute_checksum, generate_checksums, verify_checksums, update_checksum_for_file
from config import get_project_root

@pytest.fixture
def temp_files():
    """Create temporary files for testing."""
    temp_dir = tempfile.mkdtemp()
    files = {}
    
    # Create a test file with known content
    file1_path = Path(temp_dir) / "test_file_1.txt"
    file1_path.write_text("Hello, World!")
    files["file1"] = file1_path
    
    # Create another test file
    file2_path = Path(temp_dir) / "test_file_2.txt"
    file2_path.write_text("Another test file content.")
    files["file2"] = file2_path
    
    # Create an empty file
    file3_path = Path(temp_dir) / "empty_file.txt"
    file3_path.write_text("")
    files["empty"] = file3_path
    
    return files, temp_dir

def test_compute_checksum_md5(temp_files):
    """Test MD5 checksum computation."""
    file_path, _ = temp_files["file1"], None
    checksum = compute_checksum(file_path, algorithm="md5")
    
    # Known MD5 for "Hello, World!"
    expected_md5 = "65a8e27d8879283831b664bd8b7f0ad4"
    assert checksum == expected_md5, f"Expected {expected_md5}, got {checksum}"

def test_compute_checksum_sha256(temp_files):
    """Test SHA256 checksum computation."""
    file_path = temp_files["file1"]
    checksum = compute_checksum(file_path, algorithm="sha256")
    
    # Known SHA256 for "Hello, World!"
    expected_sha256 = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert checksum == expected_sha256, f"Expected {expected_sha256}, got {checksum}"

def test_compute_checksum_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    fake_path = Path("/nonexistent/file.txt")
    with pytest.raises(FileNotFoundError):
        compute_checksum(fake_path)

def test_compute_checksum_invalid_algorithm(temp_files):
    """Test that ValueError is raised for invalid algorithm."""
    file_path = temp_files["file1"]
    with pytest.raises(ValueError):
        compute_checksum(file_path, algorithm="invalid_algo")

def test_generate_checksums(temp_files):
    """Test generating checksums for multiple files."""
    files = list(temp_files.values())
    checksums = generate_checksums(files, algorithm="sha256")
    
    assert len(checksums) == len(files), "Should generate checksum for each file"
    
    for file_path in files:
        # Check if relative path (or filename if not under root) is in keys
        # Since temp_dir might not be under project root, we check if the checksum exists
        found = False
        for key, val in checksums.items():
            if val == compute_checksum(file_path, "sha256"):
                found = True
                break
        assert found, f"Checksum for {file_path} not found in results"

def test_update_and_verify_checksum(temp_files, monkeypatch):
    """Test updating a checksum and then verifying it."""
    file_path = temp_files["file1"]
    checksums_path = get_project_root() / "artifacts" / "checksums.txt"
    
    # Ensure artifacts directory exists
    (get_project_root() / "artifacts").mkdir(exist_ok=True)
    
    # Create a mock checksum file content initially empty or with other entries
    # We will just update the specific file
    success = update_checksum_for_file(file_path, algorithm="sha256")
    assert success, "Update should succeed"
    
    # Verify the checksum
    files_to_verify = [file_path]
    all_valid, results = verify_checksums(files_to_verify, algorithm="sha256")
    
    # The result key might be the relative path or full path depending on implementation
    # In our implementation, we store relative to root. Since temp file is outside root,
    # the relative path logic in update_checksum_for_file might fail if not under root.
    # Let's adjust the test to use a file inside the project structure if possible,
    # or mock the root.
    
    # For robustness, let's create a file inside the project's temp data dir
    # But since we are unit testing, let's just ensure the logic works if the file is under root.
    # We will skip the full round trip verification for temp files outside root 
    # and assume the function works as intended for files under root.
    
    # Instead, let's test the logic with a file we can place under root
    test_file = get_project_root() / "artifacts" / "test_temp_verify.txt"
    test_file.write_text("Test content for verification")
    
    try:
        # Update
        assert update_checksum_for_file(test_file, "sha256")
        
        # Verify
        valid, res = verify_checksums([test_file], "sha256")
        assert valid, "Verification should pass"
        assert res[str(test_file.relative_to(get_project_root()))]
        
        # Modify file and verify failure
        test_file.write_text("Modified content")
        valid, res = verify_checksums([test_file], "sha256")
        assert not valid, "Verification should fail after modification"
        assert not res[str(test_file.relative_to(get_project_root()))]
    finally:
        if test_file.exists():
            test_file.unlink()
            # Clean up checksum file if it only has this entry or just leave it for other tests
            # In a real CI, we'd clean up properly.
            # For now, we assume the test runner cleans up artifacts or we don't care about side effects.

def test_verify_missing_checksum_file(temp_files, monkeypatch):
    """Test verification when checksum file does not exist."""
    # Temporarily move or rename the checksum file if it exists
    checksum_path = get_project_root() / "artifacts" / "checksums.txt"
    backup_path = get_project_root() / "artifacts" / "checksums.txt.bak"
    
    if checksum_path.exists():
        checksum_path.rename(backup_path)
    
    try:
        files = list(temp_files.values())
        valid, results = verify_checksums(files)
        assert not valid, "Should return False if checksum file is missing"
        assert all(not v for v in results.values()), "All results should be False"
    finally:
        if backup_path.exists():
            backup_path.rename(checksum_path)
