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

    def test_real_tasks_md_with_const_principle_labels_classifies_real(self):
        """A real tasks.md that tags tasks with a Constitution-principle reference in
        the [Story] position ([Const VII] — e.g. PROJ-704's clinical-validation gate)
        must classify 'real'. Those are FILLED labels, not unfilled placeholders, and
        must not trip unfilled_bracket_density (a live CI audit failure)."""
        tmp = Path(tempfile.mkdtemp(prefix="tasks_const_"))
        try:
            tasks = tmp / "tasks.md"
            tasks.write_text(textwrap.dedent("""\
                # Tasks: Measuring Epistemic Resilience

                ## Phase 5: Clinical Validation (Constitution VII)

                - [ ] T041a [Const VII] [US1] Sample items from mislead_questions.jsonl.
                - [ ] T041b [Const VII] Define clinical review CSV schema in contracts/.
                - [ ] T041c [Const VII] Generate manual review instructions for two clinicians.
                - [ ] T042 [Const VII] Create validate_clinical.py to compute Cohen's kappa.
                - [ ] T043 [Const VII] Generate clinical_validation_report.md with kappa + status.
                - [ ] T044 [Const VII] Enforce gate: cannot reach research_complete without validation.
            """))
            cls, rules = classify(tasks, templates_dir=TEMPLATES_DIR)
            self.assertEqual(
                cls, "real",
                msg=f"[Const VII]-labelled tasks.md misclassified {cls}; rules: {[r.rule_id for r in rules]}",
            )
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_claim_layer_markers_do_not_classify_real_artifact_as_template(self):
        """A real artifact carrying claims-layer quality markers
        ([UNRESOLVED-CLAIM: <id> — <reason>] from specs 016-020, and the legacy
        citation-guard [UNVERIFIED: <ref> — <reason>]) must classify 'real'.
        Those markers are INTENTIONAL filled annotations, not unfilled template
        placeholders — but their bracket density previously tripped Rule 2 and
        classified the artifact 'template' (observed on PROJ-308 / PROJ-520
        tasks.md). The real-only guard refuses anything classified 'template'
        via unfilled_bracket_density, so this false-positive would BLOCK a
        legitimately-flagged project from advancing."""
        tmp = Path(tempfile.mkdtemp(prefix="claims_test_"))
        try:
            tasks = tmp / "tasks.md"
            tasks.write_text(textwrap.dedent("""\
                # Tasks: Quantifying Entanglement Entropy

                ## Phase 3: User Story 1 (Priority: P1)

                - [X] T001 [US1] Build the random-circuit sampler in code/sample.py [UNRESOLVED-CLAIM: c_4a96a144 — status=not_enough_info]
                - [X] T002 [US1] Compute entanglement entropy in code/entropy.py [UNRESOLVED-CLAIM: c_0d966b16 — status=not_enough_info]
                - [X] T003 [US1] Fit the scaling law in code/fit.py [UNRESOLVED-CLAIM: c_1b2c3d4e — status=not_enough_info]
                - [X] T004 [US2] Validate against the reference value [UNRESOLVED-CLAIM: c_5f6a7b8c — status=not_enough_info]
                - [X] T005 [US2] Compute the Renyi spectrum in code/renyi.py [UNRESOLVED-CLAIM: c_9d8e7f6a — status=not_enough_info]
                - [X] T006 [US2] Bootstrap the error bars in code/boot.py [UNRESOLVED-CLAIM: c_2a3b4c5d — status=not_enough_info]
                - [X] T007 [US3] Emit results to data/results/entropy.csv [UNVERIFIED: arXiv:2401.00001 — fetch failed]
            """))
            cls, rules = classify(tasks, templates_dir=TEMPLATES_DIR)
            self.assertEqual(
                cls, "real",
                msg=f"claim-marked tasks.md misclassified {cls}; rules: {[r.rule_id for r in rules]}",
            )
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

    def test_single_token_bracket_annotations_not_template(self):
        """Spec 014 regression: a real tasks.md the Tasker annotates with
        single-token brackets ([REVISION], [P], [US1]) must NOT trip the
        bracket-density rule (those are labels/annotations, not unfilled
        placeholders). Only multi-word descriptive placeholders count. A doc
        saturated with multi-word descriptive placeholders still classifies."""
        tmp = Path(tempfile.mkdtemp(prefix="anno_test_"))
        try:
            tasks = tmp / "tasks.md"
            tasks.write_text(
                "# Tasks: Dipole Prediction\n\n## Phase 1\n\n"
                + "".join(
                    f"- [ ] T{i:03d} [P] [US1] [REVISION] Implement step {i} in src/m{i}.py\n"
                    for i in range(1, 9)
                )
            )
            self.assertEqual(classify(tasks, templates_dir=TEMPLATES_DIR)[0], "real")

            # Multi-word descriptive placeholders in prose still flag template.
            bad = tmp / "bad.md"
            bad.write_text(
                "# Doc\n\nFill: [Alpha Value Here] [Beta Value Here] [Gamma Value Here] "
                "[Delta Value Here] [Epsilon Value Here] [Zeta Value Here] [Eta Value Here].\n"
            )
            self.assertEqual(classify(bad, templates_dir=TEMPLATES_DIR)[0], "template")
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


def test_depends_on_task_annotations_are_not_template_placeholders(tmp_path):
    """A tasks.md that expresses dependencies via explicit ``[DEPENDS ON: T0NN]``
    annotations (the filled form of a removed ``[P]`` marker) must classify REAL,
    not template. Live PROJ-492 tasker refusal: the tasker correctly switched
    mis-tagged [P] tasks to [DEPENDS ON: T0NN] and the whole tasks.md was
    mis-classified 'template' on bracket density (sample=['[DEPENDS ON: T011]', …])
    and refused. A bracket naming a concrete task id is FILLED, not a placeholder."""
    from llmxive.audit.template_vs_real import classify

    tasks = "# Tasks\n\n## Phase 1\n" + "".join(
        f"- [ ] T{i:03d} [P] [US1] do thing {i} in code/a{i}.py "
        f"[DEPENDS ON: T0{(i % 9) + 11:02d}]\n"
        for i in range(12, 30)
    )
    p = tmp_path / "tasks.md"
    p.write_text(tasks, encoding="utf-8")
    classification, rules = classify(p, templates_dir=Path(".specify/templates"))
    assert classification == "real", [r.rule_id for r in rules]


def test_genuine_unfilled_template_still_classifies_template(tmp_path):
    """Regression: the bracket-density rule must still catch a real unfilled
    template — the [DEPENDS ON: T0NN] exclusion must not blanket-disable it."""
    from llmxive.audit.template_vs_real import classify

    tmpl = (
        "# Feature Specification: [FEATURE NAME]\nCreated: [DATE]\n\n## Overview\n"
        "[Brief description of the feature]\n\n## Requirements\n"
        "[List the functional requirements here]\n[Describe the user scenarios]\n"
        "[Add acceptance criteria]\n[Define the success metrics]\n"
        "[Enumerate the edge cases]\n[Note the assumptions made]\n"
    )
    p = tmp_path / "spec.md"
    p.write_text(tmpl, encoding="utf-8")
    classification, _ = classify(p, templates_dir=Path(".specify/templates"))
    assert classification == "template"


def test_see_us_story_backrefs_are_not_template_placeholders(tmp_path):
    """`[See US-1]` is a FILLED User-Story cross-reference the specifier emits on
    every FR/SC (specifier.md mandates citing the story each serves), exactly
    analogous to `[DEPENDS ON: T011]` — NOT an unfilled placeholder. Live
    PROJ-530/PROJ-118 spec refusals: sample=['[See US-1]','[See US-1]','[See US-2]']."""
    from llmxive.audit.template_vs_real import classify

    spec = "# Spec\n\n## Requirements\n" + "".join(
        f"- FR-00{i} The system does thing {i} [See US-{(i % 3) + 1}]\n" for i in range(1, 9)
    ) + "\n## User Stories\n- US-1 As a user I can do things\n"
    p = tmp_path / "spec.md"
    p.write_text(spec, encoding="utf-8")
    classification, rules = classify(p, templates_dir=Path(".specify/templates"))
    assert classification == "real", [r.rule_id for r in rules]


def test_generic_type_annotations_classify_real(tmp_path):
    """Regression (PROJ-018, red-X'd the speckit audit): a data-model.md whose
    fields use generic type annotations — List[String], Map[String, Float], nested
    Map[String, Map[String, Float]] — classifies REAL. The unfilled-bracket
    density rule previously false-positived on these type-parameter brackets."""
    from llmxive.audit.template_vs_real import classify

    dm = (
        "# Data Model: Adoption Study\n\n## Entities\n\n### SurveyRecord\n"
        "- `practice_adoption_flags`: List[String] (adopted practices)\n"
        "- `vif_scores`: Map[String, Float] (Variance Inflation Factors)\n"
        "- `correlation_matrix`: Map[String, Map[String, Float]] (pairwise)\n"
        "- `efa_loadings`: Map[String, Map[String, Float]] (factor loadings)\n"
        "- `model_coef`: Map[String, Float] (regression coefficients)\n\n"
        "Each record is keyed by respondent id and validated against the schema.\n"
    )
    p = tmp_path / "data-model.md"
    p.write_text(dm, encoding="utf-8")
    classification, rules = classify(p, templates_dir=Path(".specify/templates"))
    assert classification == "real", [r.rule_id for r in rules]


def test_genuine_unfilled_placeholders_still_template(tmp_path):
    """The fix is PRECISE: standalone [Placeholder] tokens (space-separated, not
    glued to a preceding identifier) MUST still trip the bracket-density rule."""
    from llmxive.audit.template_vs_real import classify

    dm = (
        "# Data Model: [Entity Name Here]\n\n## Entities\n\n### [Entity One]\n"
        "- Field One: [Brief Description Here]\n- Field Two: [Another Description]\n"
        "- Field Three: [Yet Another Thing]\n- Field Four: [Describe This Field]\n"
        "- Field Five: [Some Placeholder Value]\n\n[Add More Entities Here].\n"
    )
    p = tmp_path / "data-model.md"
    p.write_text(dm, encoding="utf-8")
    classification, rules = classify(p, templates_dir=Path(".specify/templates"))
    assert classification == "template", [r.rule_id for r in rules]


# --- the bracket heuristic must not flag the agent's OWN annotations -------------
#
# `unfilled_bracket_density` counted ANY multi-word bracket, so it classified 8 real,
# fully-written specs as "unfilled templates" and failed the `audit` workflow on them
# — while contributing ZERO true positives (the one genuinely-unfilled artifact fired
# the SSoT rule, `literal_template_phrases>=3`). A gate that cries wolf 8 times out of
# 9 teaches everyone to ignore it, which is worse than having no gate.
#
# Every string below is REAL content the agents legitimately emit. Note that
# FILLED_TASK_REF_RE could not even see most of them: it required `\bT\d{2,4}\b`, so a
# SUFFIXED task id (`T029a`, `T012b`, `T006_run`) never matched — the trailing word
# character killed the boundary.
_AGENT_AUTHORED = [
    "[Requires: T029a]", "[Dep: T006_run]", "[BLOCKED UNTIL T012a PASSES]",
    "[MUST run after T001a-T001q]", "[User Story 1]", "[SPEC UPDATE]",
    "[Note: DEAP-EMG is a derived subset, not a standalone HF repo]",
    "[Preserve existing citations verbatim]",
]


def test_agent_authored_brackets_are_not_unfilled_placeholders(tmp_path) -> None:
    doc = tmp_path / "tasks.md"
    doc.write_text(
        "# Tasks — Predicting Cognitive Decline from Resting-State fMRI\n\n"
        "These tasks implement the pre-registered analysis described in spec.md.\n\n"
        + "\n".join(
            f"- [X] T{i:03d} Implement the real analysis step {b}"
            for i, b in enumerate(_AGENT_AUTHORED)
        )
        + "\n",
        encoding="utf-8",
    )
    classification, rules = classify(doc, templates_dir=Path(".specify/templates"))
    assert classification != "template", (
        f"real, fully-written content misclassified as a template: "
        f"{[r.rule_id for r in rules]}"
    )


def test_a_genuinely_unfilled_template_is_still_caught(tmp_path) -> None:
    """The real signal must survive: an artifact still carrying the TEMPLATE's own
    placeholders is a template."""
    doc = tmp_path / "spec.md"
    doc.write_text(
        "# [FEATURE NAME]\n\n**Date**: [DATE]\n\n## [Brief Title]\n\n"
        "[Link to spec.md or relevant documentation]\n\n"
        "- [Category 1]\n- [Category 2]\n",
        encoding="utf-8",
    )
    classification, rules = classify(doc, templates_dir=Path(".specify/templates"))
    assert classification == "template", [r.rule_id for r in rules]


def test_scaffold_is_not_a_defect_before_its_author_runs(tmp_path) -> None:
    """`/speckit-specify` SCAFFOLDS every artifact from the templates; each is filled
    in later at its own stage. A project at project_initialized therefore has a
    spec.md that is STILL the raw template — the Specifier has not run yet. Failing
    the audit on it makes the gate red for queue depth, not for a real problem
    (PROJ-834). Once the project reaches `specified`, the same file IS judged."""
    from llmxive.audit.template_vs_real import audit

    repo = tmp_path
    pid = "PROJ-834-x"
    spec = repo / "projects" / pid / "specs" / "001-x" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "# Feature Specification: [FEATURE NAME]\n\n"
        "**Created**: [DATE]\n**Input**: \"$ARGUMENTS\"\n\n"
        "## Overview\n[Brief description of the feature]\n"
        "[List the functional requirements here]\n[Describe the user scenarios]\n"
        "[Add acceptance criteria]\n[Define the success metrics]\n",
        encoding="utf-8",
    )
    tmpl = repo / "templates"
    tmpl.mkdir()
    (tmpl / "spec-template.md").write_text(spec.read_text(encoding="utf-8"), encoding="utf-8")
    state = repo / "state" / "projects"
    state.mkdir(parents=True)
    stage_file = state / f"{pid}.yaml"

    stage_file.write_text("current_stage: project_initialized\n", encoding="utf-8")
    m = audit(projects_dir=repo / "projects", templates_dir=tmpl, repo_root=repo)
    assert [i for i in m["items"] if i["classification"] == "template"] == [], (
        "a scaffold was failed before its authoring agent ever ran"
    )

    # Once the Specifier HAS run, the very same unfilled file IS a defect.
    stage_file.write_text("current_stage: specified\n", encoding="utf-8")
    m = audit(projects_dir=repo / "projects", templates_dir=tmpl, repo_root=repo)
    assert [i for i in m["items"] if i["classification"] == "template"], (
        "an unfilled spec at `specified` must still be caught"
    )
