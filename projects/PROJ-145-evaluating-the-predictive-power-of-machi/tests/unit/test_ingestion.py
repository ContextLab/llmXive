"""Unit tests for data ingestion and checksum validation (T005).

Checksum tests always run. Tests that touch ``code.data_ingestion`` are
skipped when that module cannot be imported (e.g. a pyarrow/numpy
incompatibility in the environment), so collection never hard-fails.
"""
import hashlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from code.compute_checksum import compute_file_checksum

try:
    from code import data_ingestion
    HAVE_DATA_INGESTION = True
except ImportError:
    data_ingestion = None
    HAVE_DATA_INGESTION = False

_SKIP = "code.data_ingestion unavailable (missing or incompatible dependency)"


def test_checksum_known_content(tmp_path):
    p = tmp_path / "sample.bin"
    p.write_bytes(b"hello hea")
    expected = hashlib.sha256(b"hello hea").hexdigest()
    assert compute_file_checksum(p) == expected


def test_checksum_detects_tampering(tmp_path):
    p = tmp_path / "sample.bin"
    p.write_bytes(b"original")
    good = compute_file_checksum(p)
    p.write_bytes(b"tampered")
    assert compute_file_checksum(p) != good


def test_checksum_empty_file(tmp_path):
    p = tmp_path / "empty.bin"
    p.write_bytes(b"")
    assert compute_file_checksum(p) == hashlib.sha256(b"").hexdigest()


@pytest.mark.skipif(not HAVE_DATA_INGESTION, reason=_SKIP)
def test_sample_holdout_known_excludes_train():
    raw = [
        {"composition": "A B C D E", "energy": -1.0},
        {"composition": "F G H I J", "energy": -2.0},
        {"composition": "K L M N O", "energy": -3.0},
        {"composition": "P Q R S T", "energy": -4.0},
    ]
    train_index = {"a b c d e"}
    sampled = data_ingestion.sample_holdout_known(raw, train_index, 2, 42)
    assert len(sampled) == 2
    for row in sampled:
        assert str(row).strip().lower() not in train_index


@pytest.mark.skipif(not HAVE_DATA_INGESTION, reason=_SKIP)
def test_load_hmao_dataset_fails_loudly():
    from unittest.mock import patch

    with patch("datasets.load_dataset") as mock_load:
        mock_load.side_effect = ConnectionError("Failed to load dataset")
        with pytest.raises(ConnectionError):
            data_ingestion.load_hmao_dataset(streaming=True)
