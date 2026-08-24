import pytest
import os
import csv
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.helpers import (
    generate_user_id,
    hash_ip,
    format_timestamp,
    get_education_code,
    truncate_user_agent,
    prepare_submission_row,
    append_to_submissions_csv,
    save_submission,
    get_submissions_csv_path,
    ensure_data_dirs,
    USER_AGENT_MAX_LENGTH
)
from datetime import datetime


def test_generate_user_id():
    user_id = generate_user_id()
    assert len(user_id) == 36  # Standard UUID length
    assert user_id.count('-') == 4


def test_hash_ip():
    ip = "192.168.1.1"
    hashed = hash_ip(ip)
    assert len(hashed) == 64  # SHA-256 hex digest length
    assert hashed == hash_ip(ip)  # Deterministic


def test_hash_ip_empty():
    assert hash_ip("") == ""


def test_format_timestamp():
    now = datetime.now()
    ts = format_timestamp(now)
    assert isinstance(ts, str)
    assert "T" in ts  # ISO format separator


def test_get_education_code():
    assert get_education_code("High School") == 1
    assert get_education_code("Bachelor's") == 2
    assert get_education_code("Master's") == 3
    assert get_education_code("PhD") == 4
    assert get_education_code("Unknown") == 0


def test_truncate_user_agent():
    long_ua = "A" * 300
    truncated = truncate_user_agent(long_ua)
    assert len(truncated) == USER_AGENT_MAX_LENGTH
    assert truncated == "A" * USER_AGENT_MAX_LENGTH

    short_ua = "Short"
    assert truncate_user_agent(short_ua) == short_ua

    assert truncate_user_agent("") == ""


def test_prepare_submission_row():
    row = prepare_submission_row(
        participant_id="p1",
        stimulus_id="s1",
        credibility=5,
        professionalism=4,
        timestamp="2023-01-01T00:00:00",
        hashed_ip="abc123",
        age=25,
        education_code=2,
        duplicate_flag=False,
        session_status="active",
        submission_status="complete"
    )
    assert row["participant_id"] == "p1"
    assert row["credibility"] == 5
    assert row["duplicate_flag"] is False


def test_append_to_submissions_csv(tmp_path, monkeypatch):
    # Monkeypatch the get_submissions_csv_path to use a temp file
    temp_csv = tmp_path / "submissions.csv"
    monkeypatch.setattr(
        "utils.helpers.get_submissions_csv_path",
        lambda: temp_csv
    )

    row = prepare_submission_row(
        participant_id="p1",
        stimulus_id="s1",
        credibility=5,
        professionalism=4,
        timestamp="2023-01-01T00:00:00",
        hashed_ip="abc123",
        age=25,
        education_code=2,
        duplicate_flag=False,
        session_status="active",
        submission_status="complete"
    )

    append_to_submissions_csv(row)

    assert temp_csv.exists()
    with open(temp_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['participant_id'] == 'p1'
        assert rows[0]['credibility'] == '5'

    # Append second row
    row2 = prepare_submission_row(
        participant_id="p2",
        stimulus_id="s2",
        credibility=3,
        professionalism=3,
        timestamp="2023-01-02T00:00:00",
        hashed_ip="def456",
        age=30,
        education_code=3,
        duplicate_flag=True,
        session_status="timeout",
        submission_status="incomplete"
    )
    append_to_submissions_csv(row2)

    with open(temp_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[1]['participant_id'] == 'p2'
        assert rows[1]['duplicate_flag'] == 'True'