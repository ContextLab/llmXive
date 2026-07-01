"""Unit tests for the plan-reviser slug-rekeying helpers (engine-failure fix).

Engine-failure issues #384/#385/#386 all crashed the pipeline engine at the
`plan` stage with::

    RuntimeError: PlanReviser: response tried to write artifacts outside the
    plan set: [...]

Two distinct root causes, both in ``_AbstractPlanReviser._parse_response``:

* #385/#386 — the reviser emitted valid plan edits under a PARAPHRASED
  project/feature-dir slug (``001-predict-...`` vs the canonical
  ``001-predicting-...``; ``abs-28814`` vs ``abs-2605-28814``). The exact
  ``path in valid_set`` check rejected them → engine crash. Fixed by re-keying
  to the canonical path via the feature-relative tail (the multi-doc analogue
  of ``pick_expected_artifact``).
* #384 — the reviser emitted ONLY the SOURCE ``spec.md`` (zero valid plan
  edits). Fixed by raising the RECOGNIZED malformed-reply shape so the engine
  degrades to "no artifact change this round" instead of crashing.

These tests exercise the pure helpers directly.
"""

from __future__ import annotations

from llmxive.convergence.revisers.plan_reviser import (
    _feature_relative_tail,
    _rekey_to_canonical,
)


def test_feature_relative_tail_plan_doc():
    assert (
        _feature_relative_tail(
            "projects/PROJ-1/specs/001-slug/plan.md"
        )
        == "plan.md"
    )


def test_feature_relative_tail_contract():
    assert (
        _feature_relative_tail(
            "projects/PROJ-1/specs/001-slug/contracts/output.schema.yaml"
        )
        == "contracts/output.schema.yaml"
    )


def test_feature_relative_tail_paper_side():
    # paper/specs/... still contains the '/specs/' segment.
    assert (
        _feature_relative_tail("PROJ-1/paper/specs/001-slug/data-model.md")
        == "data-model.md"
    )


def test_feature_relative_tail_none_when_no_specs_segment():
    assert _feature_relative_tail("src/llmxive/foo.py") is None
    assert _feature_relative_tail("plan.md") is None


def test_rekey_paraphrased_feature_slug_issue386():
    """#386: LLM used `001-predict-...`; canonical is `001-predicting-...`."""
    valid = {
        "projects/PROJ-259-predicting/specs/001-predicting-plant/plan.md",
        "projects/PROJ-259-predicting/specs/001-predicting-plant/research.md",
    }
    got = _rekey_to_canonical(
        "projects/PROJ-259-predicting/specs/001-predict-plant/plan.md", valid
    )
    assert got == "projects/PROJ-259-predicting/specs/001-predicting-plant/plan.md"


def test_rekey_paraphrased_project_and_feature_slug_issue385():
    """#385: BOTH the project dir (`abs-28814`) and feature dir differ from the
    canonical (`abs-2605-28814`) — matched by the contract tail."""
    canonical = (
        "projects/PROJ-637-https-arxiv-org-abs-2605-28814/"
        "specs/001-https-arxiv-org-abs-2605-28814/"
        "contracts/circle_packing.schema.yaml"
    )
    valid = {canonical}
    emitted = (
        "projects/PROJ-637-https-arxiv-org-abs-28814/"
        "specs/001-https-arxiv-org-abs-28814/"
        "contracts/circle_packing.schema.yaml"
    )
    assert _rekey_to_canonical(emitted, valid) == canonical


def test_rekey_source_spec_has_no_plan_tail_returns_none_issue384():
    """#384: the emitted `spec.md` has tail `spec.md`, but the valid plan set
    has no `spec.md` → no re-key candidate → None (caller rejects/degrades)."""
    valid = {"projects/PROJ-019/specs/001-gene/plan.md"}
    got = _rekey_to_canonical(
        "projects/PROJ-019/specs/001-gene-regulat/spec.md", valid
    )
    assert got is None


def test_rekey_ambiguous_tail_returns_none():
    """Two valid paths sharing the emitted tail → ambiguous → None (never
    guess which canonical path the model meant)."""
    valid = {
        "projects/P/specs/001-a/contracts/x.schema.yaml",
        "projects/P/specs/002-b/contracts/x.schema.yaml",
    }
    got = _rekey_to_canonical(
        "projects/P/specs/003-c/contracts/x.schema.yaml", valid
    )
    assert got is None
