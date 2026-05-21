"""T026: template-vs-real auditor tests against known fixtures.

Positive: tests/fixtures/audit/speckit_real/*.md classify as 'real'.
Negative: tests/fixtures/audit/speckit_template/*.md classify as 'template'.
Legacy-migration discriminator: re-tests that real prose under a templated
heading is rescued.
"""

from __future__ import annotations

import shutil
import tempfile
import textwrap
import unittest
from pathlib import Path

from llmxive.audit.template_vs_real import audit, classify


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / ".specify" / "templates"
FIXTURE_REAL = REPO_ROOT / "tests" / "fixtures" / "audit" / "speckit_real"
FIXTURE_TEMPLATE = REPO_ROOT / "tests" / "fixtures" / "audit" / "speckit_template"


class TestClassifyFixtures(unittest.TestCase):
    def test_real_fixture_classifies_as_real(self):
        path = FIXTURE_REAL / "spec.md"
        self.assertTrue(path.exists())
        cls, rules = classify(path, templates_dir=TEMPLATES_DIR)
        self.assertEqual(
            cls, "real",
            msg=f"expected real, got {cls}; rules_fired: {[r.rule_id for r in rules]}",
        )

    def test_template_fixture_classifies_as_template(self):
        path = FIXTURE_TEMPLATE / "spec.md"
        self.assertTrue(path.exists())
        cls, rules = classify(path, templates_dir=TEMPLATES_DIR)
        self.assertEqual(
            cls, "template",
            msg=f"expected template, got {cls}; rules: {[r.rule_id for r in rules]}",
        )
        # Should cite at least one of the two template signals
        rule_ids = [r.rule_id for r in rules]
        self.assertTrue(
            any("template" in rid or "bracket" in rid or "action_required" in rid for rid in rule_ids),
            f"unexpected rules_fired: {rule_ids}",
        )

    def test_legacy_migration_discriminator(self):
        """A file with the legacy migration status + substantive body classifies real."""
        tmp = Path(tempfile.mkdtemp(prefix="legacy_test_"))
        try:
            legacy = tmp / "legacy-spec.md"
            legacy.write_text(textwrap.dedent("""\
                # Feature Specification: Some Migrated Project

                **Status**: migrated from legacy technical-design (pre-refactor)

                ## Background

                """ + ("This is real, substantive prose. " * 30) + """

                ## Methods

                """ + ("Real methodology description. " * 30)
            ))
            cls, rules = classify(legacy, templates_dir=TEMPLATES_DIR)
            self.assertEqual(cls, "real")
            self.assertTrue(
                any(r.rule_id == "legacy_migration_discriminator" for r in rules)
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_table_and_diagram_heavy_data_model_classifies_real(self):
        """Spec 014 regression: a substantive data-model.md whose sections are
        an ER mermaid diagram, per-entity attribute tables, fenced CSV schemas,
        and parent headings must classify 'real' — NOT 'partial'. The previous
        body-density rule stripped fenced blocks before measuring and counted
        table/diagram-heavy sections as empty, blocking the Planner forever."""
        tmp = Path(tempfile.mkdtemp(prefix="dm_test_"))
        try:
            dm = tmp / "data-model.md"
            dm.write_text(textwrap.dedent("""\
                # Data Model: Example

                ## Entity Relationships

                ```mermaid
                erDiagram
                    CodeSegment ||--o{ CloneDensityMetric : "has"
                    CodeSegment ||--o{ ModelMetric : "has"
                ```

                ## Entity Definitions

                ### CodeSegment

                Represents a discrete unit of Python code extracted from the corpus.

                | Attribute | Type | Required | Description |
                |-----------|------|----------|-------------|
                | segment_id | string | YES | Unique identifier |
                | file_path | string | YES | Original file path |
                | ast_hash | string | YES | SHA256 of canonical AST |

                ### CloneDensityMetric

                Computed syntactic clone density for a segment.

                | Attribute | Type | Required | Description |
                |-----------|------|----------|-------------|
                | metric_id | string | YES | Unique identifier |
                | density_score | float | YES | matched / total |

                ## CSV File Schemas

                ### clone_density_metrics.csv

                ```csv
                segment_id,threshold,density_score
                abc123,0.8,0.42
                ```

                ## Data Flow

                Segments are extracted, hashed, scored for density, then evaluated
                by the model; the correlation step joins density and model metrics.
            """))
            cls, rules = classify(dm, templates_dir=TEMPLATES_DIR)
            self.assertEqual(
                cls, "real",
                msg=f"table/diagram data-model misclassified {cls}; rules: {[r.rule_id for r in rules]}",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_real_tasks_md_with_format_labels_classifies_real(self):
        """Spec 014 regression: a real tasks.md uses the required structural
        labels [P]/[US1]/[Story], which are ALSO present in tasks-template.md.
        They must NOT be learned as template placeholders, or every correctly
        formatted tasks.md would mis-classify 'template'. The tasks-template
        itself must still classify 'template' (it has real placeholders)."""
        tmp = Path(tempfile.mkdtemp(prefix="tasks_test_"))
        try:
            tasks = tmp / "tasks.md"
            tasks.write_text(textwrap.dedent("""\
                # Tasks: Evaluating Code Duplication Impact

                **Input**: Design documents from specs/001-x/

                ## Phase 1: Setup

                - [ ] T001 Create project structure in src/dup/
                - [ ] T002 [P] Configure pytest in pyproject.toml

                ## Phase 3: User Story 1 (Priority: P1)

                - [ ] T003 [P] [US1] Implement AST parser in src/dup/parser.py
                - [ ] T004 [US1] Implement clone scorer in src/dup/score.py
                - [ ] T005 [P] [US2] Add perplexity probe in src/dup/probe.py
                - [ ] T006 [US2] Wire correlation in src/dup/correlate.py
                - [ ] T007 [US3] Emit results to data/results/out.csv
            """))
            cls, rules = classify(tasks, templates_dir=TEMPLATES_DIR)
            self.assertEqual(
                cls, "real",
                msg=f"real tasks.md misclassified {cls}; rules: {[r.rule_id for r in rules]}",
            )
            # The template itself must still be caught.
            tmpl_cls, _ = classify(TEMPLATES_DIR / "tasks-template.md", templates_dir=TEMPLATES_DIR)
            self.assertEqual(tmpl_cls, "template")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_fenced_flowchart_bracket_labels_not_template(self):
        """Spec 014 regression: bracketed node labels inside a fenced block
        (a mermaid/ASCII data-flow chart, e.g. '[Dataset Download] -> ...') are
        diagram CONTENT, not unfilled [PLACEHOLDER] markers, and must not trip
        the bracket-density rule. A doc saturated with standalone bracket
        placeholders in prose must still classify template."""
        tmp = Path(tempfile.mkdtemp(prefix="flow_test_"))
        try:
            ok = tmp / "data-model.md"
            ok.write_text(textwrap.dedent("""\
                # Data Model: Example

                ## Widget

                | field | type |
                |-------|------|
                | id | string |

                ## Data Flow

                ```
                [Dataset Download] -> data/raw/
                [Clone Detection] -> data/processed/clones.csv
                [Perplexity Compute] -> data/processed/ppl.csv
                [Bug Detection Eval] -> data/results/bugs.csv
                [Correlation] -> data/results/corr.csv
                [Plotting] -> data/results/plots/
                ```
            """))
            self.assertEqual(classify(ok, templates_dir=TEMPLATES_DIR)[0], "real")

            # Standalone bracket placeholders in PROSE still flag template.
            bad = tmp / "bad.md"
            bad.write_text(
                "# Doc\n\nFill these: [Alpha Value] [Beta Value] [Gamma Value] "
                "[Delta Value] [Epsilon Value] [Zeta Value] [Eta Value].\n"
            )
            self.assertEqual(classify(bad, templates_dir=TEMPLATES_DIR)[0], "template")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_genuinely_empty_sections_still_partial(self):
        """The body-density rule must still flag headings-with-no-content so the
        bug-fix above does not weaken genuine partial detection."""
        tmp = Path(tempfile.mkdtemp(prefix="empty_test_"))
        try:
            empty = tmp / "data-model.md"
            empty.write_text(
                "# Doc\n\n## Alpha\n\n## Beta\n\n## Gamma\n\n## Delta\n\n## Epsilon\n"
            )
            cls, rules = classify(empty, templates_dir=TEMPLATES_DIR)
            self.assertEqual(
                cls, "partial",
                msg=f"empty-section doc should be partial; got {cls}; rules: {[r.rule_id for r in rules]}",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestAuditEndToEnd(unittest.TestCase):
    def setUp(self):
        # Create a tiny tmp 'projects/' tree with one template and one real artifact
        self.root = Path(tempfile.mkdtemp(prefix="audit_e2e_"))
        proj_template = self.root / "projects" / "PROJ-TEST-TPL" / "specs" / "001-x"
        proj_real = self.root / "projects" / "PROJ-TEST-REAL" / "specs" / "001-x"
        proj_template.mkdir(parents=True)
        proj_real.mkdir(parents=True)
        shutil.copy(FIXTURE_TEMPLATE / "spec.md", proj_template / "spec.md")
        shutil.copy(FIXTURE_REAL / "spec.md", proj_real / "spec.md")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_audit_classifies_both(self):
        manifest = audit(
            projects_dir=self.root / "projects",
            templates_dir=TEMPLATES_DIR,
            repo_root=self.root,
        )
        by_path = {it["target"]: it for it in manifest["items"]}
        self.assertEqual(len(by_path), 2)
        for target, item in by_path.items():
            if "PROJ-TEST-TPL" in target:
                self.assertEqual(item["classification"], "template")
            else:
                self.assertEqual(item["classification"], "real")
        self.assertEqual(manifest["summary"]["by_classification"].get("template"), 1)
        self.assertEqual(manifest["summary"]["by_classification"].get("real"), 1)


if __name__ == "__main__":
    unittest.main()
