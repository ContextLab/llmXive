import hashlib
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from data_acquisition.download_benchmark import compute_sha256, download_file, main


def test_compute_sha256():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)

    checksum = compute_sha256(tmp_path)
    expected = hashlib.sha256(b"test data").hexdigest()
    assert checksum == expected
    tmp_path.unlink()


def test_download_file(tmp_path: Path):
    url = "https://httpbin.org/delay/1"  # A reliable test URL
    dest = tmp_path / "test_download.txt"

    success, msg = download_file(url, dest)
    assert success
    assert dest.exists()
    assert dest.stat().st_size > 0


def test_main_integration(tmp_path: Path):
    # Create a mock sources.yaml
    sources_file = tmp_path / "sources.yaml"
    sources_data = {
        "benchmark": {
            "url": "https://httpbin.org/json",
            "file": "benchmark_test.json",
            "checksum": ""
        }
    }
    with open(sources_file, "w") as f:
        yaml.dump(sources_data, f)

    output_dir = tmp_path / "data" / "raw" / "benchmark"
    metadata_file = tmp_path / "metadata.yaml"

    # Mock sys.argv
    test_args = [
        "download_benchmark.py",
        "--config", str(sources_file),
        "--output-dir", str(output_dir),
        "--checksum-file", str(metadata_file)
    ]

    with patch("sys.argv", test_args):
        result = main()

    assert result == 0
    assert (output_dir / "benchmark_test.json").exists()
    assert metadata_file.exists()

    with open(metadata_file, "r") as f:
        metadata = yaml.safe_load(f)

    assert "benchmark" in metadata
    assert metadata["benchmark"]["file"] == "benchmark_test.json"
    assert "checksum" in metadata["benchmark"]
    assert len(metadata["benchmark"]["checksum"]) == 64