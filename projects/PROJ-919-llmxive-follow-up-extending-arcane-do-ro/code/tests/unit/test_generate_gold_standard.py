import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.generate_gold_standard import (
    N_SAMPLES,
    compute_sha256,
    determine_labels,
    extract_segments,
    main,
)


@pytest.fixture
def sample_text():
    # Create a mock text with enough paragraphs
    paragraphs = [f"This is paragraph {i} with some content." for i in range(100)]
    return "\n\n".join(paragraphs)


@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path


def test_sample_structure(sample_text):
    segments = extract_segments(sample_text, interval=5, count=N_SAMPLES)
    assert len(segments) == N_SAMPLES
    # Check that segments are non-overlapping and ordered
    assert "paragraph 0" in segments[0]
    assert "paragraph 5" in segments[1]
    assert "paragraph 10" in segments[2]


def test_score_range(sample_text):
    # Test that labels are generated correctly
    labels_early = determine_labels(sample_text, 0)
    assert labels_early["coarse_phase"] == "Innocence / Naive Trust"

    labels_late = determine_labels(sample_text, 15)
    assert labels_late["coarse_phase"] == "Experience / Calculated Skepticism"


def test_determinism(sample_text):
    labels1 = determine_labels(sample_text, 5)
    labels2 = determine_labels(sample_text, 5)
    assert labels1 == labels2


def test_phase_values(sample_text):
    # Test that the two halves have different phases
    labels_first_half = determine_labels(sample_text, 9)
    labels_second_half = determine_labels(sample_text, 10)

    assert labels_first_half["coarse_phase"] != labels_second_half["coarse_phase"]
    assert labels_first_half["fine_phase"] != labels_second_half["fine_phase"]


def test_checksum_computation(temp_output_dir):
    test_file = temp_output_dir / "test.json"
    test_file.write_text("test content")
    checksum = compute_sha256(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in "0123456789abcdef" for c in checksum)


@patch("scripts.generate_gold_standard.fetch_gutenberg_text")
def test_main_creates_files(mock_fetch, temp_output_dir, sample_text):
    mock_fetch.return_value = sample_text

    # Mock paths to use temp directory
    import scripts.generate_gold_standard as module

    original_output = module.OUTPUT_PATH
    original_checksum = module.CHECKSUM_PATH

    module.OUTPUT_PATH = temp_output_dir / "gold_standard.json"
    module.CHECKSUM_PATH = temp_output_dir / "gold_standard.sha256"

    try:
        checksum = main()

        assert module.OUTPUT_PATH.exists()
        assert module.CHECKSUM_PATH.exists()

        with open(module.OUTPUT_PATH, "r") as f:
            data = json.load(f)
            assert len(data) == N_SAMPLES
            assert "annotations" in data[0]
            assert "coarse" in data[0]["annotations"]
            assert "fine" in data[0]["annotations"]

        with open(module.CHECKSUM_PATH, "r") as f:
            stored_checksum = f.read()
            assert stored_checksum == checksum
    finally:
        module.OUTPUT_PATH = original_output
        module.CHECKSUM_PATH = original_checksum
