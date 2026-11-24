"""Tests for code/utils/schema_validation.py (T006).

The validators load YAML contracts from SCHEMA_DIRS; these tests
monkeypatch that list to point at temporary schema files so the
validation logic is exercised end-to-end without depending on
files produced by other tasks.
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from utils import schema_validation as sv  # noqa: E402


NEURAL_SCHEMA = {
    "required": ["subject_id", "roi", "timepoint", "signal"],
    "properties": {
        "subject_id": {"type": "string"},
        "roi": {"type": "string"},
        "timepoint": {"type": "integer"},
        "signal": {"type": "number"},
    },
}

TEXT_SCHEMA = {
    "required": ["story_id", "story"],
    "properties": {
        "story_id": {"type": "string"},
        "story": {"type": "string"},
        "event_boundaries": {"type": "array"},
    },
}

RSA_SCHEMA = {
    "required": ["roi", "similarity_score"],
    "properties": {
        "roi": {"type": "string"},
        "similarity_score": {"type": "number", "minimum": -1.0, "maximum": 1.0},
    },
}


@pytest.fixture()
def schema_dir(tmp_path, monkeypatch):
    """Point SCHEMA_DIRS at a temp dir containing the three contracts."""
    d = tmp_path / "contracts"
    d.mkdir()
    for name, schema in [
        ("neural-data.schema.yaml", NEURAL_SCHEMA),
        ("text-data.schema.yaml", TEXT_SCHEMA),
        ("rsa-output.schema.yaml", RSA_SCHEMA),
    ]:
        with open(d / name, "w", encoding="utf-8") as f:
            yaml.safe_dump(schema, f)
    monkeypatch.setattr(
        sv, "SCHEMA_DIRS", [d], raising=True
    )
    return d


def _write_csv(path, header, rows):
    with open(path, "w", encoding="utf-8") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")


def test_valid_neural_csv(schema_dir, tmp_path):
    csv_path = tmp_path / "roi_timecourses.csv"
    _write_csv(
        csv_path,
        ["subject_id", "roi", "timepoint", "signal"],
        [
            ["sub-01", "left_hipp", 0, 0.5],
            ["sub-01", "left_hipp", 1, -0.2],
            ["sub-02", "dlpfc", 0, 1.3],
        ],
    )
    report = sv.validate_data("neural", str(csv_path))
    assert report["valid"] is True
    assert report["contract"] == "neural"
    assert report["schema_file"] == "neural-data.schema.yaml"


def test_neural_csv_missing_column(schema_dir, tmp_path):
    csv_path = tmp_path / "bad.csv"
    _write_csv(csv_path, ["subject_id", "roi"], [["sub-01", "left_hipp"]])
    assert sv.validate_neural_data(str(csv_path)) is False


def test_neural_csv_non_numeric_signal(schema_dir, tmp_path):
    csv_path = tmp_path / "bad_types.csv"
    _write_csv(
        csv_path,
        ["subject_id", "roi", "timepoint", "signal"],
        [["sub-01", "left_hipp", 0, "not_a_number"]],
    )
    assert sv.validate_neural_data(str(csv_path)) is False


def test_neural_csv_header_only(schema_dir, tmp_path):
    csv_path = tmp_path / "empty.csv"
    _write_csv(
        csv_path,
        ["subject_id", "roi", "timepoint", "signal"],
        [],
    )
    assert sv.validate_neural_data(str(csv_path)) is False


def test_valid_text_jsonl(schema_dir, tmp_path):
    jsonl_path = tmp_path / "stories.jsonl"
    records = [
        {"story_id": "s1", "story": "Once upon a time.", "event_boundaries": [0, 5]},
        {"story_id": "s2", "story": "The end."},
    ]
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    report = sv.validate_data("text", str(jsonl_path))
    assert report["valid"] is True


def test_text_jsonl_missing_required_field(schema_dir, tmp_path):
    jsonl_path = tmp_path / "bad_stories.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"story": "no id here"}) + "\n")
    assert sv.validate_text_data(str(jsonl_path)) is False


def test_text_jsonl_malformed_line(schema_dir, tmp_path):
    jsonl_path = tmp_path / "broken.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write("{not valid json}\n")
    assert sv.validate_text_data(str(jsonl_path)) is False


def test_rsa_json_bounds(schema_dir, tmp_path):
    json_path = tmp_path / "rsa.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"roi": "left_hipp", "similarity_score": 0.42}, f)
    assert sv.validate_rsa_output(str(json_path)) is True

    bad_path = tmp_path / "rsa_bad.json"
    with open(bad_path, "w", encoding="utf-8") as f:
        json.dump({"roi": "left_hipp", "similarity_score": 1.5}, f)
    assert sv.validate_rsa_output(str(bad_path)) is False


def test_missing_data_file(schema_dir, tmp_path):
    assert sv.validate_neural_data(str(tmp_path / "nope.csv")) is False


def test_unknown_contract_raises(schema_dir):
    with pytest.raises(ValueError):
        sv.validate_data("bogus", None)


def test_schema_only_validation(schema_dir):
    """No data path: schema loads successfully -> True."""
    assert sv.validate_neural_data(None) is True


def test_write_validation_report(schema_dir, tmp_path):
    reports = [
        sv.validate_data("neural", None),
        sv.validate_data("text", None),
    ]
    out = tmp_path / "reports" / "validation_report.json"
    written = sv.write_validation_report(reports, str(out))
    assert written == out
    assert out.exists()
    with open(out, "r", encoding="utf-8") as f:
        payload = json.load(f)
    assert payload["all_valid"] is True
    assert len(payload["reports"]) == 2


def test_cli_valid(schema_dir, tmp_path, capsys):
    csv_path = tmp_path / "ok.csv"
    _write_csv(
        csv_path,
        ["subject_id", "roi", "timepoint", "signal"],
        [["sub-01", "left_hipp", 0, 0.1]],
    )
    rc = sv.main(["neural", str(csv_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["valid"] is True


def test_cli_invalid(schema_dir, tmp_path):
    csv_path = tmp_path / "bad.csv"
    _write_csv(csv_path, ["subject_id"], [["sub-01"]])
    assert sv.main(["neural", str(csv_path)]) == 1


def test_cli_usage(schema_dir):
    assert sv.main([]) == 2
    assert sv.main(["bogus", "x"]) == 2