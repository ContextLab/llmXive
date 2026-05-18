# Contract: ReviewRecord v2 (extends existing schema)

## Purpose

Document the additive change to `ReviewRecord` introduced by spec 012. All other fields are unchanged from the existing schema.

## New field

```yaml
# YAML frontmatter of a review file:
---
artifact_hash: ...
artifact_path: ...
backend: dartmouth
feedback: "Strong methodology; β_k missing reduces reproducibility."
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:36:36Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
action_items:                        # NEW field
  - id: a3f1c9b2e5d8
    text: "Add explicit value for hyperparameter β_k in Section 4.1."
    severity: writing
  - id: 7b4d2e1c6f90
    text: "Discuss why the unified model surpasses single-domain experts."
    severity: writing
---

# Free-form review body
...
```

## Schema rules (pydantic, in src/llmxive/types.py)

- `action_items: list[ActionItem]` with default `[]`.
- Validator (model-level):
  - If `verdict in {"minor_revision", "full_revision", "major_revision_writing", "major_revision_science", "fundamental_flaws", "reject"}` AND `reviewer_kind == "llm"` → `len(action_items) >= 1` MUST hold. Else → ValidationError.
  - If `verdict == "accept"` → `len(action_items) >= 0` (no constraint).

## Back-compat rules

- Loading an OLD `ReviewRecord` (no `action_items` field) MUST succeed with `action_items=[]`.
- The advancement evaluator's gate logic MUST treat old records (action_items=[]) as "valid review, contributes no items to revision plan." Old `accept` records still satisfy the all-accept gate.

## Test commitments

- A round-trip test (`tests/unit/test_review_record_action_items.py`) MUST cover: emit → serialize to YAML → re-parse → validate identity.
- A back-compat test MUST cover: load an existing review file from `projects/PROJ-564/paper/reviews/` (which has no action_items field) and confirm it loads with action_items=[].
