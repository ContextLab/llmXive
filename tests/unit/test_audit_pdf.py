"""T047: PDF auditor unit + integration tests.

Uses real PDFs from docs/papers/ (Constitution III: real-world testing).
Verifies:
  - auditor walks PDFs and emits a valid manifest
  - every defect carries the required FR-013 shape
  - the supported-PDFs registry is rewritten with zero-defect entries
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from llmxive.audit.pdf_auditor import audit

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_PAPERS = REPO_ROOT / "docs" / "papers"

#: Audit a bounded SAMPLE of real PDFs, not the entire live tree. docs/papers/
#: grows unboundedly as the pipeline produces papers (174 PDFs x ~5s each =
#: ~15 min PER test, which silently 30-min-stalled the suite). A handful of real
#: PDFs still exercises the auditor end-to-end (Constitution III) while staying
#: fast — and an isolated repo_root means the live papers/.supported.json
#: registry is never mutated as a test side-effect.
_SAMPLE_SIZE = 3


@unittest.skipUnless(DOCS_PAPERS.exists() and any(DOCS_PAPERS.rglob("*.pdf")),
                     "no PDFs under docs/papers/ — skipping live audit")
class TestPdfAuditorOnLivePdfs(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = Path(tempfile.mkdtemp())
        cls.SAMPLE = cls._tmp / "docs" / "papers"
        cls.SAMPLE.mkdir(parents=True)
        for src in sorted(DOCS_PAPERS.rglob("*.pdf"))[:_SAMPLE_SIZE]:
            dst = cls.SAMPLE / src.relative_to(DOCS_PAPERS)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def test_audit_produces_valid_manifest(self):
        manifest = audit(papers_dir=self.SAMPLE, repo_root=self._tmp)
        self.assertIn("items", manifest)
        self.assertGreater(manifest["summary"]["total"], 0)
        # Each item carries paper_id + classification + (rules_fired or defects)
        for item in manifest["items"]:
            self.assertIn(item["classification"], ("passes", "fails"))
            self.assertIn("rules_fired", item)
            for defect in item.get("defects", []):
                # FR-013: every defect carries the required shape
                self.assertIn("paper_id", defect)
                self.assertIn("page", defect)
                self.assertGreaterEqual(defect["page"], 1)
                self.assertIn("defect_type", defect)
                self.assertIn(defect["defect_type"], (
                    "unevaluated_command", "section_numbering", "reference_style",
                    "figure_size_inconsistency", "author_block_inconsistency",
                    "link_style", "custom_block_misrender",
                ))
                self.assertIn("evidence_snippet", defect)
                self.assertGreater(len(defect["evidence_snippet"]), 0)
                self.assertIn("rule_id", defect)

    def test_registry_written_on_audit(self):
        audit(papers_dir=self.SAMPLE, repo_root=self._tmp)
        reg = self._tmp / "papers" / ".supported.json"
        self.assertTrue(reg.exists())
        data = json.loads(reg.read_text())
        self.assertIn("auditor_version", data)
        self.assertIn("audited_at", data)
        self.assertIn("entries", data)
        # Every entry has the FR-022 shape
        for e in data["entries"]:
            self.assertIn("paper_id", e)
            self.assertIn("last_passed_at", e)


class TestPdfAuditorMissingDirRaises(unittest.TestCase):
    def test_missing_papers_dir(self):
        with self.assertRaises(FileNotFoundError):
            audit(papers_dir="/nonexistent/path", repo_root=REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
