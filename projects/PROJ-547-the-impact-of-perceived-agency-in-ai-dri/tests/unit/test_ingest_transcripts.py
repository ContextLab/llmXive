import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from agency_scoring.ingest_transcripts import ingest_transcripts


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    data = "session_id,utterances\n1,\"[\\\"Hello\\\", \\\"How are you?\\\"]\"\n2,\"[\\\"I feel fine.\\\"]\""
    p = tmp_path / "sample.csv"
    p.write_text(data, encoding="utf-8")
    return p


@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    records = [
        {"session_id": "a", "utterances": ["Hi", "What's up?"]},
        {"session_id": "b", "utterances": ["Good morning"]},
    ]
    p = tmp_path / "sample.json"
    p.write_text(json.dumps(records), encoding="utf-8")
    return p


def test_ingest_csv(sample_csv: Path):
    df = ingest_transcripts(sample_csv)
    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {"session_id", "utterances"}
    assert len(df) == 2


def test_ingest_json(sample_json: Path):
    df = ingest_transcripts(sample_json)
    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {"session_id", "utterances"}
    assert len(df) == 2


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        ingest_transcripts("nonexistent_file.csv")