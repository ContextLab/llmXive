"""Build per-panel labeled calibration sets (spec 015 T067).

For each reviewable stage we need a small labeled corpus:

- **positives**: clean artifacts the panel SHOULD accept (no concerns).
- **negatives**: artifacts the panel SHOULD reject (each carrying a
  known injected flaw + a sidecar JSON noting the expected lens).

This module composes the seed positives below with the
:mod:`llmxive.calibration.injectors` to produce the labeled negatives.
Drivers (T068) consume the seed set + drive the panel + diff verdicts
through :mod:`llmxive.calibration.differential`.

The seed positives are deliberately small + synthetic — they are NOT
the anchor papers from :mod:`llmxive.calibration.domains` (those are
the "real domain anchor" verification set). The synthetic seeds exist
so the calibration harness can run offline without paper-corpus access.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .injectors import INJECTORS, Injection

# --- Seed positives (clean artifacts) ------------------------------------


_IDEA_POSITIVE = """\
# Idea — synthetic seed (calibration positive)

Research question: Does a multi-task LLM panel produce better-calibrated
review verdicts than a single-reviewer panel under matched compute?

Related work: prior single-reviewer benchmarks (e.g., the original LLM-
based code review systems) report low agreement with human reviewers.
Multi-task / multi-lens panels have been studied in human peer review
literature but not systematically in LLM contexts.

Feasibility: implementable with existing convergence engine + free
Dartmouth Chat backend; data exists in llmXive's own evaluation traces.
"""

_SPEC_POSITIVE = """\
# Spec — synthetic seed (calibration positive)

## User Story
US1: As a maintainer I want a calibration verdict per panel so I can
target prompt adjustments.

## Functional Requirements
- FR-001: System MUST emit one calibration verdict per injector run.
- FR-002: System MUST persist the adjudication checklist to disk for
  the maintainer to review.

## Success Criteria
- SC-001: 100% of injections in the calibration set produce a verdict
  (no silent drops), measured by `tests/unit/test_differential_calibration.py`.
"""

_PLAN_POSITIVE = """\
# Plan — synthetic seed (calibration positive)

## Methodology
Compare clean-vs-injected verdicts per stage, repeated for noise-
robustness. Use the differential calibration adjudication report as the
single source of truth for prompt-adjustment decisions.

## Datasets
- llmXive evaluation traces (already on disk; no external download).
- The 9 anchor papers from `llmxive.calibration.domains` (DOIs in the
  module; manual lookup required at T068 adjudication).

## Plan ↔ data-model coherence
The CalibrationRun dataclass mirrors the FR-001/FR-002 fields exactly.

## Constitution Check
- Principle V (real-call testing): satisfied by T068 real-qwen runs.
- Principle II (honest reporting): satisfied by the "missed injection
  → false negative" surface in the report.
"""

_TASKS_POSITIVE = """\
# Tasks — synthetic seed (calibration positive)

- [ ] T001 [FR-001]: System MUST emit one calibration verdict per
  injector run. Implementation in `calibration/differential.py`.
  Verification: `tests/unit/test_differential_calibration.py::
  test_calibration_run_caught_when_expected_lens_in_injected_concerns`.

- [ ] T002 [FR-002]: System MUST persist the adjudication checklist
  to disk for the maintainer to review. Implementation: write the
  `to_markdown()` output to `specs/015-pipeline-convergence-protocol/
  calibration/adjudication-<domain>.md`. Verification:
  `tests/unit/test_differential_calibration.py::
  test_adjudication_report_markdown_includes_every_run_section`.
"""

_PAPER_POSITIVE = """\
# Paper section — synthetic seed (calibration positive)

In this work we evaluate a multi-task LLM convergence panel. We
report verdicts on a held-out anchor paper (Tibshirani 1996,
DOI 10.1111/j.2517-6161.1996.tb02080.x) and find that the panel
correctly identifies the Lasso paper as a positive contribution under
all of its lenses.
"""


_SEED_POSITIVES: dict[str, str] = {
    "idea": _IDEA_POSITIVE,
    "spec": _SPEC_POSITIVE,
    "plan": _PLAN_POSITIVE,
    "tasks": _TASKS_POSITIVE,
    "paper": _PAPER_POSITIVE,
}


# Which injectors apply to which stage. The unused-on-this-stage
# injectors are intentionally skipped (e.g. the circular_rq injector
# requires an idea-style artifact; running it on a plan doesn't make
# sense).
#
# Entries are ``(injector_name, expected_lens_override | None)``. The
# override exists because some injectors are appropriate on multiple
# stages but the lens that SHOULD catch them differs by stage. For
# example, ``gutted_requirement`` weakens MUST→should markers; on the
# TASKS stage this is a ``constraint_preservation`` violation (the
# tasks dropped the spec's constraint), but on the SPEC stage itself
# the same change is a ``requirements_coverage`` issue (the spec no
# longer requires what it should). The injector's default
# ``expected_lens`` comes from its registry entry in ``injectors.py``;
# this map can override it per stage.
_STAGE_INJECTORS: dict[str, tuple[tuple[str, str | None], ...]] = {
    "idea": (("circular_rq", None),),
    "spec": (("gutted_requirement", "requirements_coverage"),),
    "plan": (("fabricated_data", None), ("plan_tasks_contradiction", None)),
    "tasks": (("fr_without_task", None), ("gutted_requirement", None)),
    "paper": (("nonexistent_citation", None),),
}


# --- Builder --------------------------------------------------------------


@dataclass(frozen=True)
class CalibrationSetEntry:
    """One file in a per-panel calibration set."""

    stage: str
    label: str
    """Either ``"positive"`` (clean artifact) or
    ``f"negative_{injector_name}"`` (artifact with a specific injected flaw)."""
    text: str
    expected_lens: str | None
    """``None`` for positives; the lens the panel should flag for negatives."""
    description: str


def build_set_for_stage(stage: str) -> list[CalibrationSetEntry]:
    """Build the labeled calibration set for one stage: one positive +
    one negative per applicable injector."""
    positive_text = _SEED_POSITIVES.get(stage)
    if positive_text is None:
        raise ValueError(
            f"no seed positive for stage {stage!r}; expected one of "
            f"{list(_SEED_POSITIVES)!r}"
        )
    entries: list[CalibrationSetEntry] = [
        CalibrationSetEntry(
            stage=stage,
            label="positive",
            text=positive_text,
            expected_lens=None,
            description=f"Synthetic clean {stage} artifact (calibration positive).",
        ),
    ]
    for injector_name, lens_override in _STAGE_INJECTORS.get(stage, ()):
        fn, default_lens = INJECTORS[injector_name]
        injection: Injection = fn(positive_text)  # type: ignore[operator]
        # Per-stage lens override (see comment on _STAGE_INJECTORS); if
        # the stage doesn't override it, fall back to the injector's
        # default lens from its INJECTORS registry entry.
        effective_lens = lens_override or default_lens
        entries.append(
            CalibrationSetEntry(
                stage=stage,
                label=f"negative_{injector_name}",
                text=injection.text,
                expected_lens=effective_lens,
                description=injection.description,
            )
        )
    return entries


def write_set_for_stage(stage: str, output_dir: Path) -> list[Path]:
    """Write the calibration set for ``stage`` to ``output_dir/<stage>/``.

    Each entry produces TWO files:

    - ``<label>.md`` — the artifact text (drop-in for panel runs).
    - ``<label>.label.json`` — the metadata (expected_lens + description).

    Returns the list of written paths."""
    entries = build_set_for_stage(stage)
    stage_dir = output_dir / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for entry in entries:
        md_path = stage_dir / f"{entry.label}.md"
        md_path.write_text(entry.text)
        sidecar_path = stage_dir / f"{entry.label}.label.json"
        sidecar_path.write_text(
            json.dumps({
                "stage": entry.stage,
                "label": entry.label,
                "expected_lens": entry.expected_lens,
                "description": entry.description,
            }, indent=2) + "\n"
        )
        written.extend([md_path, sidecar_path])
    return written


def write_all(output_dir: Path) -> list[Path]:
    """Build + write the labeled calibration set for every stage that has
    a seed positive. Returns every written path."""
    all_written: list[Path] = []
    for stage in _SEED_POSITIVES:
        all_written.extend(write_set_for_stage(stage, output_dir))
    return all_written


__all__ = [
    "CalibrationSetEntry",
    "build_set_for_stage",
    "write_all",
    "write_set_for_stage",
]
