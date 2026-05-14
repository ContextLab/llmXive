"""T015: round-trip audit-manifest through writer + JSON Schema validator.

Verifies:
    - new_manifest() produces a dict matching the schema's required header
    - add_item() preserves required fields + summary counters
    - write_manifest() emits valid JSON to the right path
    - missing required header fields raises ValueError (fail-fast, Principle V)
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import jsonschema

from llmxive.audit.manifest import (
    ManifestItem,
    RuleFired,
    Defect,
    add_item,
    new_manifest,
    read_manifest,
    write_manifest,
)


def _load_schema() -> dict:
    repo = Path(__file__).resolve().parents[2]
    schema_path = repo / "specs" / "009-quality-fixes-pass" / "contracts" / "audit-manifest.schema.json"
    return json.loads(schema_path.read_text())


class TestManifestSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = _load_schema()
        cls.tmp = Path(tempfile.mkdtemp(prefix="manifest_test_"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_empty_manifest_is_valid(self):
        m = new_manifest("personality_rubric")
        jsonschema.validate(m, self.schema)

    def test_classification_item_round_trip(self):
        m = new_manifest("template_vs_real")
        add_item(m, ManifestItem(
            target="projects/PROJ-TEST/specs/001-x/spec.md",
            rules_fired=[RuleFired(rule_id="literal_template_phrases>=3", evidence_snippet="hits=4")],
            classification="template",
        ))
        jsonschema.validate(m, self.schema)
        self.assertEqual(m["summary"]["by_classification"]["template"], 1)

    def test_defect_item_round_trip(self):
        m = new_manifest("pdf")
        add_item(m, ManifestItem(
            target="papers/foo.pdf",
            rules_fired=[RuleFired(rule_id="pdf_audit", evidence_snippet="2 defect(s)")],
            classification="fails",
            defects=[
                Defect(paper_id="foo", page=1, defect_type="unevaluated_command",
                       evidence_snippet="\\autoref{fig:1}", rule_id="latex_command_in_text"),
                Defect(paper_id="foo", page=3, defect_type="section_numbering",
                       evidence_snippet="section 2 after section 4", rule_id="section_non_monotonic"),
            ],
        ))
        jsonschema.validate(m, self.schema)
        self.assertEqual(m["summary"]["by_defect_type"]["unevaluated_command"], 1)
        self.assertEqual(m["summary"]["by_defect_type"]["section_numbering"], 1)

    def test_rubric_scores_item_round_trip(self):
        m = new_manifest("personality_rubric")
        add_item(m, ManifestItem(
            target="01ARZ3NDEKTSV4RRFFQ69G5FAA",
            rules_fired=[RuleFired(rule_id="dispatch_valid", evidence_snippet="ok")],
            classification="passes",
            rubric_scores={"voice": 2, "critical_judgement": 2, "curatorial_pointer": 3, "honesty": 3},
        ))
        jsonschema.validate(m, self.schema)

    def test_write_and_read_round_trip(self):
        m = new_manifest("feedback_loop")
        add_item(m, ManifestItem(
            target="some-dispatch",
            rules_fired=[RuleFired(rule_id="dispatch_valid", evidence_snippet="ok")],
            classification="passes",
        ))
        path = write_manifest(m, self.tmp)
        self.assertTrue(path.exists())
        round_tripped = read_manifest(path)
        jsonschema.validate(round_tripped, self.schema)
        # Markdown sibling also written
        md_path = path.with_suffix(".md")
        self.assertTrue(md_path.exists())
        self.assertIn("Audit Manifest", md_path.read_text())

    def test_missing_required_header_raises(self):
        bad = {"auditor": "personality_rubric"}  # missing nearly everything
        with self.assertRaises(ValueError):
            write_manifest(bad, self.tmp)

    def test_unknown_auditor_rejected_by_constructor(self):
        with self.assertRaises(ValueError):
            new_manifest("not_a_real_auditor")


if __name__ == "__main__":
    unittest.main()
