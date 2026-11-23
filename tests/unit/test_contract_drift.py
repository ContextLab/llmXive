"""Cross-document scientific-contract drift must block, with no false alarms.

The drifting text below is quoted VERBATIM from the frozen PROJ-9999 totient
canary trial of 2026-10-09 (platform `1d2b4287245cf12cdb01ff9d367d9157229101ca`;
spec.md sha256 26737f3d7ec6442dfa412d7f1783fe0da525f5b34878938a264056db1633bf2c,
plan.md 5af66bf25b4e0e1fa2dc2ac4e09cc188ea24d8808d0fa0046dbef08bf5abfcb7,
tasks.md 9dac42d4a4bec2749f02ef8a43455a4b6c10829a17711fde2ade9f15f5800219),
including its non-breaking hyphens and its ``½``/``·`` characters — the exact
bytes a free model emits. The negative cases are likewise real text, taken from
the shapes that this scanner flagged across the repository's 745 live feature
directories before it was tightened.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.speckit._contract_drift import scan_contract_drift

# --- the observed drift (verbatim) ---------------------------------------

#: The excerpts live under ``tests/fixtures/`` because they must keep the
#: EXACT bytes a free model emitted — non-breaking hyphens, a minus sign, a
#: vulgar fraction and a multiplication sign. ``ruff.toml`` excludes that
#: directory for this reason (linting verbatim evidence would corrupt it),
#: and the digests below make a silent edit to the evidence fail loudly.
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "contract-drift-proj9999-20261009"
EXCERPT_SHA256 = {
    "spec.md": "f87146588d5889f7e42bd8eabe0e7a2ccba6023ec7be9ebad727c1a8a82e7c0a",
    "plan.md": "67178ec23e5158d918a04b72aad6b5ee119a6019cf61470b3a1c4f57cd9ecda7",
    "tasks.md": "0bceb6bcc1e4f5a43bd8283a88abdc23690e83c7363cf4621d58999eb03aeec4",
}
SPEC = (FIXTURES / "spec.md").read_text(encoding="utf-8")
PLAN = (FIXTURES / "plan.md").read_text(encoding="utf-8")
TASKS = (FIXTURES / "tasks.md").read_text(encoding="utf-8")
#: Characters spelled by codepoint so this module stays ASCII.
MULTIPLICATION_SIGN = chr(0x00D7)
GREEK_DELTA = chr(0x0394)


@pytest.mark.parametrize("name", sorted(EXCERPT_SHA256))
def test_the_frozen_excerpts_are_unmodified(name):
    import hashlib

    actual = hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()
    assert actual == EXCERPT_SHA256[name]


def test_the_canary_factor_of_two_is_reported():
    findings = {f.name: f for f in scan_contract_drift(
        {"spec.md": SPEC, "plan.md": PLAN, "tasks.md": TASKS}
    )}
    assert "stratum_TV" in findings
    expressions = dict(findings["stratum_TV"].definitions)
    assert expressions["tasks.md"] == "0.5*Abs(f_i-1/(p-1))"
    assert expressions["plan.md"] == "Abs(f_i-1/(p-1))"
    assert "not algebraically equal" in findings["stratum_TV"].reason


def test_a_dropped_absolute_value_is_reported():
    """PROJ-468: the plan takes the absolute value, the spec does not."""
    findings = scan_contract_drift({
        "spec.md": f"Dissipation = ({GREEK_DELTA}KE + {GREEK_DELTA}PE) for each run.\n",
        "plan.md": f"Dissipation is |{GREEK_DELTA}KE + {GREEK_DELTA}PE|, reported per network.\n",
    })
    assert [f.name for f in findings] == ["Dissipation"]


def test_findings_are_order_independent():
    docs = {"spec.md": SPEC, "plan.md": PLAN, "tasks.md": TASKS}
    forward = scan_contract_drift(docs)
    reverse = scan_contract_drift(dict(reversed(list(docs.items()))))
    assert [f.name for f in forward] == [f.name for f in reverse]
    assert [f.definitions for f in forward] == [f.definitions for f in reverse]


# --- things that must NOT be reported ------------------------------------

NEGATIVE_CASES: list[tuple[str, dict[str, str]]] = [
    (
        "one document cannot disagree with itself",
        {"spec.md": SPEC + PLAN + TASKS},
    ),
    (
        "a document may restate its own definition",
        {
            "spec.md": "ratio = 0.5*Abs(x)\nratio = Abs(x)/2\n",
            "plan.md": "ratio = Abs(x)/2\n",
        },
    ),
    (
        "algebraically equal restatements",
        {"spec.md": "score_mean = 0.5*Abs(d_i)\n", "plan.md": "score_mean = Abs(d_i)/2\n"},
    ),
    (
        "the same product written with a multiplication sign",
        {
            "spec.md": "contribution = count * stratum_TV\n",
            "plan.md": f"contribution = count {MULTIPLICATION_SIGN} stratum_TV\n",
        },
    ),
    (
        "a symbol in one document and its value in the other (PROJ-300)",
        {"plan.md": "L_phys = (60*6371)\n", "tasks.md": "L_phys = (scale_factor*6371)\n"},
    ),
    (
        "a renamed operand, same arithmetic (PROJ-735)",
        {"plan.md": "E_corrected = E_base+s*E_D3_term\n", "tasks.md": "E_corrected = E_base+s*E_D3\n"},
    ),
    (
        "prose joined by slashes (PROJ-011, PROJ-043)",
        {
            "spec.md": "N_valid is samples/draws retained after screening.\n",
            "tasks.md": "N_valid is original/refactored/baseline counts.\n",
        },
    ),
    (
        "a parenthesised tool list (PROJ-043)",
        {
            "spec.md": "complexity_baseline is (pylint/radon) output.\n",
            "plan.md": "complexity_baseline is radon_output/file_count\n",
        },
    ),
    (
        "italicised prose (PROJ-1051)",
        {
            "plan.md": "benchmark_set is *conditionally* used for calibration.\n",
            "tasks.md": "benchmark_set is held_out/calibration\n",
        },
    ),
    (
        "a requirement cross-reference is not arithmetic (PROJ-941)",
        {
            "plan.md": "sampling_temperature is fixed at the documented value (FR-008).\n",
            "tasks.md": "sampling_temperature is written to results/runs/run_\n",
        },
    ),
    (
        "a context-dependent single symbol (k is p, or p-1)",
        {
            "spec.md": "where k = p for the unconditional reference\n",
            "plan.md": "where k = p - 1 for the conditional reference\n",
        },
    ),
    (
        "a formula never spans a line break (PROJ-200)",
        {
            "spec.md": "Formula: `adolescent_exposure_ratio = listens_adolescence / total_listens`\n**Note**: see below.\n",
            "tasks.md": "Formula: `adolescent_exposure_ratio = adolescent_listens / total_listens`\n",
        },
    ),
    ("no documents", {}),
    ("a single empty document", {"spec.md": ""}),
]


@pytest.mark.parametrize(
    "docs", [case[1] for case in NEGATIVE_CASES], ids=[case[0] for case in NEGATIVE_CASES],
)
def test_no_false_alarm(docs):
    assert scan_contract_drift(docs) == []


# --- convergence-engine wiring -------------------------------------------

SPEC_KEY = "projects/PROJ-9999-totient-canary/specs/001-totient/spec.md"
PLAN_KEY = "projects/PROJ-9999-totient-canary/specs/001-totient/plan.md"
TASKS_KEY = "projects/PROJ-9999-totient-canary/specs/001-totient/tasks.md"


def _concerns(artifacts, stage):
    from llmxive.convergence.engine import _contract_drift_concerns

    return _contract_drift_concerns(artifacts, stage=stage, reviewer="claim_guard")


@pytest.mark.parametrize("stage", ["planned", "tasked", "paper_planned", "paper_tasked"])
def test_drift_blocks_at_every_doc_authoring_gate(stage):
    from llmxive.convergence.types import Severity

    concerns = _concerns({SPEC_KEY: SPEC, PLAN_KEY: PLAN, TASKS_KEY: TASKS}, stage)
    assert concerns, f"{stage} must block on a contract conflict"
    names = [c for c in concerns if "stratum_TV" in c.text]
    assert names, [c.text for c in concerns]
    concern = names[0]
    # SCIENCE outranks REQUIREMENT, so the doc-stage writing-only allowance
    # can never advance a factor-of-two disagreement.
    assert concern.severity is Severity.SCIENCE
    assert "0.5*Abs(f_i-1/(p-1))" in concern.text
    assert "Abs(f_i-1/(p-1))" in concern.text
    assert concern.round == 1
    assert all(len(c.id) <= 12 for c in concerns)
    assert len({c.id for c in concerns}) == len(concerns)


@pytest.mark.parametrize("stage", ["clarified", "paper_clarified", "research_review", "in_progress"])
def test_other_stages_do_not_run_the_cross_document_check(stage):
    assert _concerns({SPEC_KEY: SPEC, PLAN_KEY: PLAN, TASKS_KEY: TASKS}, stage) == []


def test_sentinel_context_inputs_are_not_compared():
    """``__spec_md__`` duplicates spec.md as a control input, not a produced doc."""
    assert _concerns({PLAN_KEY: PLAN, "__spec_md__": SPEC, "__constitution__": ""}, "planned") == []


def test_only_spec_plan_tasks_are_compared():
    assert _concerns(
        {
            "projects/P/specs/001-x/research.md": SPEC,
            "projects/P/specs/001-x/quickstart.md": PLAN,
        },
        "planned",
    ) == []


def test_agreeing_documents_raise_no_concern():
    assert _concerns({SPEC_KEY: TASKS, TASKS_KEY: TASKS}, "tasked") == []
