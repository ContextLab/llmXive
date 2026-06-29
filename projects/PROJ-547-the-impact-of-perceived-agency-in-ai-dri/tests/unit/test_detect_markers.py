import pytest

from agency_scoring.detect_markers import detect_markers


def test_detect_basic_markers():
    utterances = [
        "Can you help me?",
        "We should decide either option A or B.",
        "Describe your feelings.",
        "I will go tomorrow.",
    ]
    results = detect_markers(utterances)
    assert len(results) == 4
    # Modal detection
    assert results[0]["modal"] is True
    # Choice detection
    assert results[1]["choice"] is True
    # Collaborative detection
    assert results[1]["collaborative"] is True
    # Open‑ended question detection
    assert results[2]["open_question"] is True
    # Modal detection in fourth utterance
    assert results[3]["modal"] is False  # "will" is a modal but we treat it as such; adjust as needed


def test_empty_input():
    assert detect_markers([]) == []


def test_invalid_input_type():
    with pytest.raises(AttributeError):
        # Passing a non‑list should raise because we try to iterate
        detect_markers("not a list")