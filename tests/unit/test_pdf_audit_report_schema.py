"""T036: validate PDF audit reports against schema."""

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
    / "pdf_audit_report.schema.json"
)


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


PASS_REPORT = {
    "pdf_path": "docs/papers/PROJ-001-foo/main-llmxive.pdf",
    "paper_id": "PROJ-001-foo",
    "audited_at": "2026-05-15T01:23:45Z",
    "total_pages": 14,
    "pages": [
        {"page": i, "status": "pass", "failures": []} for i in range(1, 15)
    ],
    "summary": {
        "total_failures": 0,
        "failure_classes": {
            "source_fixable": 0,
            "unsupported_construct": 0,
            "source_missing": 0,
            "audit_tool_crash": 0,
        },
        "passed_pages": 14,
        "failed_pages": 0,
    },
}

FAIL_REPORT = {
    "pdf_path": "docs/papers/PROJ-002-bar/main-llmxive.pdf",
    "paper_id": "PROJ-002-bar",
    "audited_at": "2026-05-15T01:23:45Z",
    "total_pages": 5,
    "pages": [
        {"page": 1, "status": "pass", "failures": []},
        {
            "page": 2,
            "status": "fail",
            "failures": [
                {
                    "kind": "non_square_bracket_cite",
                    "evidence": "(Smith, 2024)",
                    "class": "source_fixable",
                    "recommendation": "normalize_references should rewrite",
                }
            ],
        },
        {"page": 3, "status": "pass", "failures": []},
        {"page": 4, "status": "pass", "failures": []},
        {"page": 5, "status": "pass", "failures": []},
    ],
    "summary": {
        "total_failures": 1,
        "failure_classes": {
            "source_fixable": 1,
            "unsupported_construct": 0,
            "source_missing": 0,
            "audit_tool_crash": 0,
        },
        "passed_pages": 4,
        "failed_pages": 1,
    },
}


class TestPDFAuditReportSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = _schema()

    def test_pass_report_valid(self) -> None:
        jsonschema.validate(PASS_REPORT, self.schema)

    def test_fail_report_valid(self) -> None:
        jsonschema.validate(FAIL_REPORT, self.schema)

    def test_invalid_failure_kind_rejected(self) -> None:
        bad = json.loads(json.dumps(FAIL_REPORT))
        bad["pages"][1]["failures"][0]["kind"] = "made_up_kind"
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(bad, self.schema)

    def test_invalid_failure_class_rejected(self) -> None:
        bad = json.loads(json.dumps(FAIL_REPORT))
        bad["pages"][1]["failures"][0]["class"] = "not_a_class"
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(bad, self.schema)


if __name__ == "__main__":
    unittest.main()
