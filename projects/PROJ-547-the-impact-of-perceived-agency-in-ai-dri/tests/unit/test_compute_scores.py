import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml

from agency_scoring.compute_scores import compute_agency_scores, _load_weights


@pytest.fixture
def sample_transcripts():
    data = {
        "session_id": ["s1", "s2", "s3"],
        "utterances": [
            ["I can help you.", "We should decide."],
            ["What do you think?", "Either option A or B?"],
            [],  # Empty transcript
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def weight_file(tmp_path: Path) -> Path:
    weights = {"modal": 1.0, "choice": 0.5, "collaborative": 0.3, "open_question": 0.8}
    p = tmp_path / "agency_weights.yaml"
    p.write_text(yaml.safe_dump(weights), encoding="utf-8")
    return p


def test_load_weights(weight_file: Path):
    w = _load_weights(weight_file)
    assert isinstance(w, dict)
    assert w["modal"] == 1.0


def test_compute_agency_scores(sample_transcripts: pd.DataFrame, weight_file: Path):
    weights = _load_weights(weight_file)
    scores_df = compute_agency_scores(sample_transcripts, weights)
    assert isinstance(scores_df, pd.DataFrame)
    assert set(scores_df.columns) == {"session_id", "agency_score"}
    # Ensure scores are within [0, 1]
    assert scores_df["agency_score"].between(0, 1).all()
    # Empty transcript should yield 0.0
    empty_score = scores_df.loc[scores_df["session_id"] == "s3", "agency_score"].iloc[0]
    assert empty_score == 0.0