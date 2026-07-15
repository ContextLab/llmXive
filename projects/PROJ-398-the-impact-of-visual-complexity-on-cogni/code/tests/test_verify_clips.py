"""
Unit tests for ``src.experiment.verify_clips``.
"""

import json
from pathlib import Path
import tempfile

import pytest

# Import the function under test
from src.experiment.verify_clips import verify_clips


@pytest.fixture
def temp_environment():
    """
    Creates a temporary directory structure with a dummy clip file and an empty
    ``research.md``. Yields paths needed for the test and cleans up afterwards.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)

        # Create a fake clips directory with a single file
        clips_dir = base / "clips"
        clips_dir.mkdir(parents=True)
        clip_path = clips_dir / "dummy_clip.txt"
        clip_path.write_text("hello world", encoding="utf-8")

        # Path for the checksum manifest
        checksum_output = base / "checksums.json"

        # Empty research markdown file
        research_md = base / "research.md"
        research_md.touch()

        yield {
            "clips_dir": clips_dir,
            "checksum_output": checksum_output,
            "research_md": research_md,
        }


def test_verify_clips_creates_checksum_and_updates_research(temp_environment):
    env = temp_environment
    dataset_url = "https://huggingface.co/datasets/HuggingFaceM4/video-conference-backgrounds"
    version_id = "v1.0.0"

    # Run the verification logic
    verify_clips(
        clips_dir=env["clips_dir"],
        checksum_output=env["checksum_output"],
        research_md=env["research_md"],
        dataset_url=dataset_url,
        version_id=version_id,
    )

    # -------------------------------------------------
    # 1. Verify checksum manifest
    # -------------------------------------------------
    assert env["checksum_output"].exists(), "Checksum JSON file was not created"
    manifest = json.loads(env["checksum_output"].read_text(encoding="utf-8"))
    assert "dummy_clip.txt" in manifest, "Checksum entry missing for the clip"

    # Compute expected checksum directly using the utility
    from src.lib.utils import compute_file_checksum

    expected_checksum = compute_file_checksum(env["clips_dir"] / "dummy_clip.txt")
    assert manifest["dummy_clip.txt"] == expected_checksum

    # -------------------------------------------------
    # 2. Verify research.md contains the metadata block
    # -------------------------------------------------
    research_content = env["research_md"].read_text(encoding="utf-8")
    assert "## Dataset Information" in research_content
    assert f"- dataset_url: {dataset_url}" in research_content
    assert f"- version_id: {version_id}" in research_content