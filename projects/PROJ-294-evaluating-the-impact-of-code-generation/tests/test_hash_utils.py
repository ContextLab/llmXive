import os
import tempfile
from code.utils.hash_utils import hash_file, verify_file_hash

def test_hash_and_verify():
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name

    try:
        # Compute hash using the utility
        computed_hash = hash_file(tmp_path)

        # Verify that the same hash is reported as valid
        assert verify_file_hash(tmp_path, computed_hash)

        # Alter the file and ensure verification fails
        with open(tmp_path, "ab") as f:
            f.write(b"corruption")
        assert not verify_file_hash(tmp_path, computed_hash)
    finally:
        os.remove(tmp_path)
