import json
from pathlib import Path

import pytest

from code.validation.reference_validator import run_reference_validation


@pytest.fixture
def temp_citations_and_sources(tmp_path: Path):
    """
    Create temporary citations and primary sources JSON files for testing.
    Returns paths (citations_path, sources_path).
    """
    citations = [
        {"title": "Gaze cueing of attention: Visual attention, social cognition, and individual differences"},
        {"title": "Emotion detection in faces using deep learning"},
    ]

    sources = [
        {"title": "Gaze cueing of attention: Visual attention, social cognition, and individual differences"},
        {"title": "Emotion detection in faces using deep learning"},
    ]

    citations_path = tmp_path / "citations.json"
    sources_path = tmp_path / "primary_sources.json"

    with open(citations_path, "w", encoding="utf-8") as f:
        json.dump(citations, f)

    with open(sources_path, "w", encoding="utf-8") as f:
        json.dump(sources, f)

    return citations_path, sources_path


def test_reference_validation_passes(temp_citations_and_sources):
    citations_path, sources_path = temp_citations_and_sources

    # Use a high threshold to ensure strict matching; the titles are identical so should pass
    report = run_reference_validation(
        citations_path=citations_path,
        sources_path=sources_path,
        output_path=Path("/dev/null"),  # we don't need the output file for the test
        threshold=0.9
    )
    assert report["status"] == "passed"
    assert report["validated"] == len(json.loads(citations_path.read_text()))


def test_reference_validation_fails_on_low_overlap(tmp_path: Path):
    # Create mismatching citation and source
    citations = [{"title": "A completely unrelated title about cats"}]
    sources = [{"title": "Deep learning for medical image segmentation"}]

    citations_path = tmp_path / "citations.json"
    sources_path = tmp_path / "primary_sources.json"

    with open(citations_path, "w", encoding="utf-8") as f:
        json.dump(citations, f)

    with open(sources_path, "w", encoding="utf-8") as f:
        json.dump(sources, f)

    # Use the default threshold 0.7; these should not match
    report = run_reference_validation(
        citations_path=citations_path,
        sources_path=sources_path,
        output_path=Path("/dev/null"),
        threshold=0.7
    )
    assert report["status"] == "failed"
    assert report["validated"] == 0
    assert report["unvalidated"] == 1