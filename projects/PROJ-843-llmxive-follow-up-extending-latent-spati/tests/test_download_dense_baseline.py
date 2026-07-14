import hashlib
import os
from pathlib import Path

from eval.download_dense_baseline import download_dense_baseline, calculate_sha256

def test_download_dense_baseline(tmp_path, monkeypatch):
    """
    Download the dense baseline to a temporary location and verify the
    SHA‑256 checksum matches the expected value (the checksum is mocked
    to avoid a real network request in CI).
    """
    # Mock requests.get to return deterministic content
    class DummyResponse:
        def __init__(self, content: bytes):
            self.content = content
            self.status_code = 200
        
        def raise_for_status(self):
            pass
        
        def iter_content(self, chunk_size=8192):
            # Yield the content in one chunk
            yield self.content
    
    dummy_content = b"dummy numpy data"
    dummy_sha = hashlib.sha256(dummy_content).hexdigest()

    def dummy_get(*args, **kwargs):
        return DummyResponse(dummy_content)

    monkeypatch.setattr("requests.get", dummy_get)

    dest = tmp_path / "dense.npy"
    # Use the dummy checksum to verify the integrity check works
    download_dense_baseline(
        url="http://example.com/dummy.npy",
        dest_path=dest,
        expected_sha256=dummy_sha,
    )
    assert dest.is_file()
    # Verify checksum function works
    assert calculate_sha256(dest) == dummy_sha