# Implementation Plan: Deterministic Claim Caching + Planning-Stage Reference-Only Verification

**Branch**: `020-deterministic-claim-caching` | **Date**: 2026-06-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/020-deterministic-claim-caching/spec.md`

## Summary

Re-architect the claim-verification stack (specs 016→019) along two axes, **reusing** the
existing machinery rather than duplicating it:

- **Part A — planning = references-only + strip/smooth.** Thread an explicit *stage class*
  signal (planning = specify/clarify/plan/tasks) from the speckit commands down into the claim
  layer. In a planning stage the layer verifies **citations only**; for any detected low-level
  claim (numeric / magnitude / relational / causal / entity-fact) it neither fetches, grounds,
  nor kicks back — it **strips and smooths** the claim into a higher-level statement (LLM rewrite
  → re-detect guard → deterministic clause-removal fallback) so no unverified/false value remains
  *and* nothing blocks. References still fail-closed via the existing reference validator. Update
  the producing templates/prompts so low-level numbers rarely appear at all.
- **Part B — deterministic frozen cache.** Make a VERIFIED claim immutable: key reuse by the
  value-independent `subject_key` (not the text-hash `claim_id`), return the frozen value without
  re-resolution unless the source hash genuinely changed, never re-open a VERIFIED record on a
  transient failure or a pending re-extraction, drop `resolved_value` from the fill cache key, and
  carry the verified value in the canonical stored document as a **durable placeholder** (resolved
  to a value only in a rendered view produced at review time and final publish). The git-tracked
  `state/claims/` registry is the single frozen source of truth.

Accuracy stays paramount: references are verified everywhere, and the paper/implementation-stage
freeze is *stronger* (deterministic + immutable) than today. Only the *location* of low-level-claim
verification changes — out of planning.

## Technical Context

**Language/Version**: Python 3.11 (existing `src/llmxive/` package; `pyproject.toml`)
**Primary Dependencies**: existing in-repo modules only — `claims/` (models, classify, canonical,
pointer, extract, resolve, service), `fill/` (service, subject_query, channels), `state/claims.py`
registry, `agents/reference_validator.py`, `speckit/` commands + `_stage_panel`, `backends/router.py`
(`reasoning_chat`). No new third-party dependency.
**Storage**: git-tracked YAML registries — `state/claims/<PROJECT-ID>.yaml` (claim records, the
frozen store), `state/citations/<PROJECT-ID>.yaml` (reference validator). The gitignored
`state/grounding-cache/` remains a within-run optimization, **not** the system of record.
**Testing**: pytest. Offline tests pin the deterministic-caching + strip/smooth + stage-gating logic;
real-call tests (`LLMXIVE_REAL_TESTS=1` + Dartmouth key, free models only) exercise the
externally-dependent paths (reference resolution, paper-stage fill/ground, strip/smooth rewrite).
**Target Platform**: Linux/macOS CLI + GitHub Actions (the pipeline runner).
**Project Type**: single-project library + CLI (the llmXive pipeline). No web/mobile surface.
**Performance Goals**: planning-stage wall-clock spent on low-level-claim fetch/ground/kickback →
**zero** (SC-001); zero re-resolutions of an already-verified fact across ≥3 rounds (SC-003) and
across a clean-checkout re-run (SC-004).
**Constraints**: no mocks on externally-dependent paths (Principle III); reuse-not-duplicate
(Principle I, FR-015); references fail-closed (Principle V, FR-004); zero regression on the
proven-good paper-stage paths — exact knot count, constants, entity facts (FR-014/SC-005).
**Scale/Scope**: the claim layer runs on every speckit artifact for 600+ projects; the change is
behavior-gating + identity/freeze + a rendering boundary, touching ~9 source modules + 4 template/
prompt families + per-project template copies.

### Key code anchors (verified this session)

| Concern | Location | Today | Change |
|-|-|-|-|
| Per-artifact claim entry | [slash_command.py:207,286](../../src/llmxive/speckit/slash_command.py#L207) | `process_document(...)` stage-blind | thread `stage` |
| Claim pipeline | [service.py:135-284](../../src/llmxive/claims/service.py#L135) | uniform all-kinds | planning gate + strip/smooth |
| Reuse key | [service.py:92](../../src/llmxive/claims/service.py#L92) | text-hash `claim_id` | value-independent `subject_key` |
| Self-heal re-resolve | [service.py:94-107](../../src/llmxive/claims/service.py#L94-L107) | re-resolves non-VERIFIED | never re-open VERIFIED (FR-011) |
| Subject-key reuse | [service.py:186-207](../../src/llmxive/claims/service.py#L186-L207) | inherits VERIFIED twin | promote to primary frozen lookup |
| Render | [pointer.py:168-207](../../src/llmxive/claims/pointer.py#L168) | bakes value into prose | durable placeholder + rendered view |
| Strip artifacts | [extract.py:42-63](../../src/llmxive/claims/extract.py#L42) | deletes `{{claim:id}}` | preserve durable placeholders |
| Classify | [classify.py:76-101](../../src/llmxive/claims/classify.py#L76) | CITATION vs low-level | reuse as the planning gate axis |
| subject_key | [canonical.py:142-176](../../src/llmxive/claims/canonical.py#L142) | value-independent | reuse as identity (FR-009) |
| Fill cache key | [fill/service.py:115-130](../../src/llmxive/fill/service.py#L115) | includes `resolved_value` | drop value (FR-012) |
| Fillable gate | [fill/service.py:281,307-311](../../src/llmxive/fill/service.py#L281) | `_FILLABLE_KINDS` | add planning short-circuit |
| Fact fingerprint | [subject_query.py:141-195](../../src/llmxive/fill/subject_query.py#L141) | all numeric tokens | value-excluded key |
| Reference gate | [reference_validator.py:177,232](../../src/llmxive/agents/reference_validator.py#L177) | `has_blocking_citations` | unchanged (still runs in planning) |
| Stage labels | clarify/plan/tasks `_cmd.py` `stage_label=` | `"spec"/"clarify"/"plan"/"tasks"`/`"paper_*"` | source of the stage class |
| Env flags | [cli.py:46,52,60](../../src/llmxive/cli.py#L46) | unconditional | unchanged (orthogonal to stage class) |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **I. Single Source of Truth (NON-NEGOTIABLE)** — PASS. FR-015 mandates reuse: the change extends
  `subject_key`, `classify`, `_FILLABLE_KINDS`, the `state/claims/` registry, and the reference
  validator in place. The one genuinely new unit — the strip/smooth transform — lives in a single
  canonical module and is called from the one planning-gate site. No forked configs, no parallel
  claim store. The stage-class predicate is defined once and threaded.
- **II. Verified Accuracy (NON-NEGOTIABLE)** — PASS (strengthened). References are still verified
  everywhere (FR-004, fail-closed). Planning no longer *leaves* a possibly-false low-level value in
  the document — it strips it (FR-002a), so accuracy improves. Paper-stage verification is unchanged
  in coverage and *stronger* in stability (frozen/immutable). FR-014/SC-005 forbid weakening any
  proven-good path.
- **III. Robustness & Reliability (Real-World Testing)** — PASS. FR-016 + Phase-1 quickstart require
  real-call tests for the external paths (reference resolution, paper-stage fill/ground, the
  strip/smooth LLM rewrite) and offline tests for the deterministic logic. No mock is the primary
  verification path.
- **IV. Cost Effectiveness (Free-First)** — PASS (net reduction). Planning skips the expensive
  fetch+ground+kickback loop on low-level claims; the freeze eliminates redundant re-resolutions.
  The only added cost is one LLM rewrite per low-level claim that still slips into a planning doc —
  far cheaper than the loop it replaces, and rarer once US3 prevention lands. Free models only.
- **V. Fail Fast** — PASS. References remain fail-closed; the stage class is decided before any
  expensive claim operation; an unresolvable citation surfaces immediately.
- **VI. Convergent Review (NON-NEGOTIABLE)** — PASS. The convergence protocol is untouched; this
  removes *dishonest* kickbacks (a low-level number exhausting the cap toward escalation over
  something that doesn't gate progress) while preserving the reference gate. Convergence still
  reports honestly.

**Result: no violations.** Complexity Tracking below records the two deliberate design costs.

## Project Structure

### Documentation (this feature)

```text
specs/020-deterministic-claim-caching/
├── plan.md              # This file
├── research.md          # Phase 0 — design decisions (stage signal, strip/smooth, freeze, placeholder, cache key)
├── data-model.md        # Phase 1 — Claim identity/lifecycle, Verified store, Placeholder, Stage class, Transform
├── quickstart.md        # Phase 1 — the real-call + offline verification matrix
├── contracts/
│   └── claim-layer-contracts.md   # Phase 1 — internal function contracts that change
├── checklists/
│   └── requirements.md  # spec-quality checklist (already complete)
└── tasks.md             # Phase 2 — /speckit-tasks output (NOT created here)
```

### Source Code (repository root) — files this feature touches

```text
src/llmxive/
├── claims/
│   ├── service.py         # stage-gated process_document; frozen subject_key reuse; strip/smooth call site
│   ├── stage.py           # NEW (single SSoT): StageClass + is_planning_stage(stage_label)
│   ├── smooth.py          # NEW (single SSoT): strip_and_smooth(passage, claim, *, backend, model)
│   ├── resolve.py         # frozen-lookup short-circuit; honor stage gate for low-level kinds
│   ├── pointer.py         # render(): canonical→durable placeholder; render_view(): values for review/publish
│   ├── extract.py         # strip_claim_artifacts: preserve durable placeholders (don't delete)
│   ├── canonical.py       # subject_key reused as identity (no change to the primitive)
│   └── models.py          # Claim identity helpers; durable-placeholder token format
├── fill/
│   ├── service.py         # drop resolved_value from cache key; planning short-circuit in fill gate
│   ├── subject_query.py   # value-excluded fingerprint/key
│   └── channels/__init__.py  # channels_for(kind, *, stage) — planning yields no low-level channels
├── speckit/
│   ├── slash_command.py   # SlashCommandContext.stage; thread to _validate_artifact_citations → process_document
│   ├── clarify_cmd.py / plan_cmd.py / tasks_cmd.py   # pass stage_label as the planning class
│   └── _stage_panel.py    # render_view for the reviewer-facing artifact at review time
├── state/
│   └── claims.py          # registry: add subject_key-keyed frozen lookup (load_verified_by_subject)
├── agents/
│   └── reference_validator.py   # unchanged behavior; confirmed to still run in planning
└── cli.py                 # unchanged (env flags orthogonal to stage class)

.specify/templates/{spec-template.md, plan-template.md}     # defer empirical specifics (FR-006)
.claude/skills/speckit-{specify,clarify,plan,tasks}/SKILL.md # RQ+method+references guidance (FR-006)
agents/prompts/panels/panel_plan_data_resources.md           # planning-doc scope guidance (FR-006)
projects/PROJ-552-*/.specify/templates/{spec,plan}-template.md  # per-project copies (FR-006)

tests/
├── unit/         # stage gate, strip/smooth idempotence, frozen lookup, value-independent cache key, placeholder round-trip
└── integration/  # planning-skip + reference-still-gated; paper-stage no-regress; cross-round/cross-run freeze
```

**Structure Decision**: Single project, existing `src/llmxive/` package. Two new single-purpose
modules (`claims/stage.py`, `claims/smooth.py`) are the only new files — every other change is an
in-place extension of a canonical module, per Principle I and FR-015. The new modules are *new
concepts* (stage classification; the strip/smooth transform) with no existing equivalent to fold
into, so they are genuinely new SSoT units rather than duplicates.

## Complexity Tracking

> No constitution **violations**. These are deliberate, spec-mandated design costs recorded for transparency.

| Design cost | Why needed (spec) | Simpler alternative rejected because |
|-|-|-|
| Durable placeholder in stored doc + separate rendered view | FR-007, FR-008, clarification Q4 | "Keep baking values into prose" was the *root cause* of waffling — the baked value is re-extracted as a new claim each round. A durable placeholder is the only way to make the stored form non-re-extractable while keeping a human-readable rendered view. |
| New LLM rewrite call (strip/smooth) in planning | FR-002a, clarification Q2 | "Just skip low-level claims" leaves a possibly-false value sitting unverified in the doc (the maintainer explicitly rejected this). "Pure regex deletion" can't smooth load-bearing sentences grammatically. LLM rewrite + re-detect guard + deterministic fallback is the minimal mechanism that guarantees claim-free *and* grammatical output. |
| Keeping per-project `.specify/templates/` copies in sync (T028) rather than de-duplicating them (Principle I tension) | FR-006 mandates updating "any per-project template copies"; speckit's `create-new-feature.sh` copies the shared templates into each project on creation, so the copies are the files PROJ-552's commands actually read | De-duplicating the per-project copies (symlink/include the shared templates) is a change to speckit's feature-scaffolding mechanism affecting all 600+ projects — out of scope for this claim-layer spec. The honest interim is to keep them in sync (FR-006) and record a **follow-up** to centralize template provisioning. Until then this is a *recorded, justified* pre-existing duplication, not a new one introduced by this spec. |
