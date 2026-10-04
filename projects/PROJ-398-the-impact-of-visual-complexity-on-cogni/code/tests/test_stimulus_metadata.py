"""
Unit test for ``src.metrics.record_metadata``.

The test executes the metadata recording script and then verifies that
a JSON side‑car file exists for every image in ``data/stimuli/raw`` and
that each file contains the three required keys.
"""

import json
from pathlib import Path

import pytest

# Import the function under test
from src.metrics.record_metadata import record_metadata


@pytest.fixture(scope="module")
def raw_stimuli_dir() -> Path:
    """Path to the directory containing raw stimulus images."""
    return Path("data/stimuli/raw")


@pytest.fixture(scope="module")
def metadata_dir() -> Path:
    """Path where metadata JSON files are stored."""
    return Path("data/stimuli/metadata")


def test_metadata_files_exist(raw_stimuli_dir: Path, metadata_dir: Path):
    """
    Ensure that for each image in the raw directory a corresponding
    ``<image_id>.json`` file exists and contains ``entropy``,
    ``color_variance`` and ``object_count``.
    """
    # Pre‑condition – the raw directory must contain at least one image.
    image_paths = list(raw_stimuli_dir.glob("*"))
    assert image_paths, f"No stimulus images found in {raw_stimuli_dir!s}"

    # Run the metadata extraction script.
    record_metadata(raw_dir=raw_stimuli_dir, metadata_dir=metadata_dir)

    # Verify that a side‑car JSON file exists for each image and that it
    # contains the expected keys.
    required_keys = {"entropy", "color_variance", "object_count"}

    for img_path in image_paths:
        json_path = metadata_dir / f"{img_path.stem}.json"
        assert json_path.is_file(), f"Missing metadata file {json_path!s}"

        with json_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)

        missing = required_keys - data.keys()
        assert not missing, f"Metadata file {json_path!s} missing keys: {missing}"