"""T023: validate speckit_artifact_audit reports against schema."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "010-personality-taste-speckit-real-pdf-audit"
    / "contracts"
    / "speckit_artifact_audit.schema.json"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


REAL_REPORT = {
    "audited_at": "2026-05-15T01:23:45Z",
    "total_artifacts": 2,
    "artifacts": [
        {
            "path": "projects/PROJ-001-foo/specs/001-foo/spec.md",
            "classification": "REAL",
            "reason": "",
            "project_id": "PROJ-001-foo",
            "stage": "specified",
            "transitive_dependents": [],
        },
        {
            "path": "projects/PROJ-002-bar/specs/002-bar/spec.md",
            "classification": "TEMPLATE",
            "reason": "literal_template_phrases>=3",
            "project_id": "PROJ-002-bar",
            "stage": "specified",
            "transitive_dependents": [
                "projects/PROJ-002-bar/specs/002-bar/plan.md"
            ],
        },
    ],
    "summary": {
        "real": 1,
        "template": 1,
        "templates_with_dependents": 1,
        "projects_to_roll_back": 1,
    },
}

EMPTY_REPORT = {
    "audited_at": "2026-05-15T01:23:45Z",
    "total_artifacts": 0,
    "artifacts": [],
    "summary": {
        "real": 0,
        "template": 0,
        "templates_with_dependents": 0,
        "projects_to_roll_back": 0,
    },
}

INVALID_MISSING_SUMMARY = {
    "audited_at": "2026-05-15T01:23:45Z",
    "total_artifacts": 0,
    "artifacts": [],
}


class TestSpeckitAuditSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = _schema()

    def test_real_report_valid(self) -> None:
        jsonschema.validate(REAL_REPORT, self.schema)

    def test_empty_report_valid(self) -> None:
        jsonschema.validate(EMPTY_REPORT, self.schema)

    def test_missing_summary_fails(self) -> None:
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(INVALID_MISSING_SUMMARY, self.schema)


if __name__ == "__main__":
    unittest.main()
