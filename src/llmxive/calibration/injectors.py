"""Flaw injectors for differential panel calibration (spec 015 T064).

Each injector is a pure function that takes a clean artifact (a string,
typically the contents of ``spec.md`` / ``plan.md`` / ``tasks.md`` / a
research-side paper section) and returns an :class:`Injection` record:
the mutated text + the lens the panel SHOULD flag it under + a
human-readable description of what was changed.

The injectors are **deterministic** — the same input always yields the
same output — so the calibration harness can re-run them across multiple
panel invocations and compare verdicts without noise from the injector
itself.

The 6 flaw types come from the design SSoT
(specs/015-pipeline-convergence-protocol/spec.md FR-038 / FR-046):

| # | Flaw | Expected lens | Stage |
|-|-|-|-|
| 1 | Trivial / circular RQ | ``rq_validity`` | idea |
| 2 | FR without a task | ``coverage`` | tasks |
| 3 | Gutted requirement | ``constraint_preservation`` | tasks |
| 4 | Fabricated data | ``data_resources`` | plan |
| 5 | Nonexistent citation | ``claim_accuracy`` | paper |
| 6 | Plan ↔ tasks contradiction | ``plan_consistency`` | plan |

Each injector is self-contained — calibration drivers can call any
subset without coordination.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

# --- Injection record -----------------------------------------------------


@dataclass(frozen=True)
class Injection:
    """The result of one injector call.

    Attributes:
        text: the mutated artifact text (drop-in replacement for the
            original; calibration drivers write this to disk + run the
            panel on it).
        expected_lens: the lens name the panel SHOULD flag this under;
            consumed by the differential adjudication report.
        description: human-readable summary of what was changed; used
            by the markdown adjudication report.
        original: a verbatim copy of the original input text; persisted
            so the adjudication report can show clean-vs-injected diffs.
    """

    text: str
    expected_lens: str
    description: str
    original: str


# Type alias for the lens-name vocabulary used across the 6 injectors.
# Mirrors the lens names in ``llmxive.convergence.reviewspecs``.
LensName = Literal[
    "rq_validity",
    "coverage",
    "constraint_preservation",
    "data_resources",
    "claim_accuracy",
    "plan_consistency",
]


# --- Injectors ------------------------------------------------------------


def inject_circular_rq(idea_text: str) -> Injection:
    """Flaw #1 — replace the research question with a circular one.

    A circular research question assumes its own answer. The idea
    panel's ``rq_validity`` lens should flag it as a SCIENCE-class
    concern (the question itself is broken, not the writing).

    The injector rewrites any line beginning with ``Research question:``
    (or the first non-empty line if no such marker exists) to use the
    canonical circular phrasing.
    """
    circular_rq = (
        "Research question: Why is the model accurate? "
        "We posit it is accurate because it is accurate."
    )
    lines = idea_text.splitlines()
    out_lines: list[str] = []
    replaced = False
    for line in lines:
        if (not replaced
            and (line.strip().lower().startswith("research question:")
                 or line.strip().startswith("- Research question:"))):
            indent = re.match(r"^\s*-?\s*", line).group(0)  # type: ignore[union-attr]
            out_lines.append(f"{indent}{circular_rq}")
            replaced = True
        else:
            out_lines.append(line)
    if not replaced:
        # No RQ marker — prepend the circular RQ as a new line at the top.
        out_lines.insert(0, circular_rq)
    return Injection(
        text="\n".join(out_lines),
        expected_lens="rq_validity",
        description=(
            "Replaced the research question with a circular phrasing "
            "('accurate because accurate'). Expected lens: rq_validity "
            "(SCIENCE-class — the question itself is broken)."
        ),
        original=idea_text,
    )


def inject_fr_without_task(tasks_text: str) -> Injection:
    """Flaw #2 — add a phantom ``FR-999`` reference to spec but ensure no task covers it.

    Drops a sentinel into ``tasks.md`` claiming a new requirement
    (FR-999) exists in the spec, but emits no task referencing it.
    The ``coverage`` tasks lens should flag this as
    REQUIREMENT-class.
    """
    sentinel_line = (
        "<!-- INJECTED CALIBRATION FLAW: FR-999 declared in spec but "
        "NO task in this file references it. The coverage lens should "
        "flag this as a REQUIREMENT-class concern. -->"
    )
    # Prepend the sentinel as a top comment so the panel reading the
    # tasks artifact can see the deliberate gap.
    return Injection(
        text=sentinel_line + "\n\n" + tasks_text,
        expected_lens="coverage",
        description=(
            "Declared FR-999 (in a comment line) without adding a task "
            "referencing it. Expected lens: coverage "
            "(REQUIREMENT-class — orphaned requirement)."
        ),
        original=tasks_text,
    )


_WEAKENING_MAP: tuple[tuple[str, str], ...] = (
    (r"\bMUST\b", "should"),
    (r"\bmust\b", "may"),
    (r"\bSHALL\b", "may"),
    (r"\bshall\b", "may"),
    (r"\brequired\b", "optional"),
    (r"\bREQUIRED\b", "OPTIONAL"),
    (r"\bexactly\b", "approximately"),
)


def inject_gutted_requirement(tasks_text: str) -> Injection:
    """Flaw #3 — weaken FR/SC strength markers in the tasks document.

    Replaces MUST → should, required → optional, exactly → approximately,
    etc. The ``constraint_preservation`` tasks lens should flag this as
    REQUIREMENT-class.

    The injector aborts (returns the input unchanged + flagged) if there
    are no recognizable strength markers to weaken; calibration drivers
    can detect this via the description string and skip the run.
    """
    out = tasks_text
    n_changes = 0
    for pattern, replacement in _WEAKENING_MAP:
        new_out, count = re.subn(pattern, replacement, out)
        n_changes += count
        out = new_out
    desc_base = (
        "Weakened requirement-strength markers (MUST → should; "
        "required → optional; exactly → approximately). "
        "Expected lens: constraint_preservation "
        "(REQUIREMENT-class — silent constraint relaxation)."
    )
    if n_changes == 0:
        return Injection(
            text=tasks_text,
            expected_lens="constraint_preservation",
            description=(
                "[INJECTION NO-OP] No strength markers found to weaken. "
                + desc_base
            ),
            original=tasks_text,
        )
    return Injection(
        text=out,
        expected_lens="constraint_preservation",
        description=f"{desc_base} {n_changes} markers weakened.",
        original=tasks_text,
    )


def inject_fabricated_data(plan_text: str) -> Injection:
    """Flaw #4 — replace dataset references with a fabricated identifier.

    Injects a reference to a deliberately-fake dataset
    (``OpenNeuro ds999999``) that the dataset_resolver pre-filter
    should fail on first; if the panel reaches the lens, the
    ``data_resources`` plan lens should flag it as METHODOLOGY-class.

    If no dataset section exists, appends a Datasets section.
    """
    fake_ds = "OpenNeuro ds999999 (FABRICATED — does not exist)"
    if re.search(r"OpenNeuro\s+ds\d+", plan_text):
        new_text = re.sub(
            r"OpenNeuro\s+ds\d+", fake_ds, plan_text, count=1,
        )
        n = 1
    elif "Datasets" in plan_text or "datasets" in plan_text:
        # Inject into an existing datasets section.
        new_text = plan_text + f"\n- {fake_ds}\n"
        n = 1
    else:
        new_text = (
            plan_text + "\n\n## Datasets\n\n- "
            + fake_ds + "\n"
        )
        n = 1
    return Injection(
        text=new_text,
        expected_lens="data_resources",
        description=(
            f"Injected reference to {fake_ds!r}. The dataset_resolver "
            "pre-filter should fail on it; if the panel reaches the lens, "
            "data_resources should flag it as METHODOLOGY-class. "
            f"({n} dataset reference replaced/added)."
        ),
        original=plan_text,
    )


def inject_nonexistent_citation(paper_text: str) -> Injection:
    """Flaw #5 — inject a citation to a paper that doesn't exist.

    Drops a sentinel ``[FabricatedAuthor2024]`` (matching the
    ``[Author2024]`` evidence pattern the triage module uses) into the
    paper text, claiming it cites a paper that doesn't exist. The
    ``claim_accuracy`` paper lens (or the citation-verifier
    pre-filter) should flag it as SCIENCE-class.
    """
    fake_cite = (
        "[FabricatedAuthor2024] (this citation is deliberately "
        "fabricated for calibration — no such paper exists)"
    )
    # Inject before the first occurrence of a sentence-ending period
    # in the body; if none, append at the end.
    m = re.search(r"\.(\s+)", paper_text)
    if m:
        idx = m.start() + 1
        new_text = paper_text[:idx] + " " + fake_cite + paper_text[idx:]
    else:
        new_text = paper_text + "\n\n" + fake_cite + "\n"
    return Injection(
        text=new_text,
        expected_lens="claim_accuracy",
        description=(
            "Injected a fabricated citation [FabricatedAuthor2024]. "
            "Expected lens: claim_accuracy (SCIENCE-class — claim "
            "supported by a non-existent paper)."
        ),
        original=paper_text,
    )


def inject_plan_tasks_contradiction(plan_text: str) -> Injection:
    """Flaw #6 — inject a contradiction between plan + tasks into the plan.

    Adds a sentinel claim into ``plan.md`` that the methodology is
    "supervised regression" while implying the tasks file (unchanged)
    uses unsupervised clustering. The ``plan_consistency`` plan lens
    should flag this as METHODOLOGY-class.

    Note: this injector only mutates the plan side; the calibration
    driver is expected to pair the injected plan with the original tasks
    file (which doesn't match) before running the panel.
    """
    contradiction_block = (
        "\n\n## INJECTED METHODOLOGY ASSERTION\n\n"
        "**Plan methodology:** supervised regression with labeled "
        "outcomes (the tasks file declares unsupervised clustering — "
        "this disagreement should be flagged by plan_consistency).\n"
    )
    return Injection(
        text=plan_text + contradiction_block,
        expected_lens="plan_consistency",
        description=(
            "Added a methodology assertion to plan.md that contradicts "
            "the tasks file (plan says supervised regression; tasks "
            "implies unsupervised clustering). Expected lens: "
            "plan_consistency (METHODOLOGY-class — plan↔tasks "
            "disagreement)."
        ),
        original=plan_text,
    )


# --- registry --------------------------------------------------------------


# Registry of every injector: name → (callable, expected_lens). Drivers
# iterate this when running the differential calibration so the full set
# is exercised without per-injector wiring code.
INJECTORS: dict[str, tuple[object, str]] = {
    "circular_rq": (inject_circular_rq, "rq_validity"),
    "fr_without_task": (inject_fr_without_task, "coverage"),
    "gutted_requirement": (inject_gutted_requirement, "constraint_preservation"),
    "fabricated_data": (inject_fabricated_data, "data_resources"),
    "nonexistent_citation": (inject_nonexistent_citation, "claim_accuracy"),
    "plan_tasks_contradiction": (inject_plan_tasks_contradiction, "plan_consistency"),
}


__all__ = [
    "INJECTORS",
    "Injection",
    "LensName",
    "inject_circular_rq",
    "inject_fabricated_data",
    "inject_fr_without_task",
    "inject_gutted_requirement",
    "inject_nonexistent_citation",
    "inject_plan_tasks_contradiction",
]
