# Phase 0 Research: Deterministic Claim Caching + Planning-Stage Reference-Only Verification

All "NEEDS CLARIFICATION" from the spec were resolved in the `## Clarifications` session
(2026-06-04). This document records the design decisions, each grounded in the **actual** current
code (verified this session), with rationale and the alternatives rejected.

---

## D1 — How the planning-stage signal is threaded (FR-001)

**Decision**: Add a single canonical predicate `claims/stage.py::is_planning_stage(stage_label: str)
-> bool` over the existing `stage_label` strings, and thread an explicit `stage_label: str | None`
parameter from `SlashCommandContext` → `_validate_artifact_citations` → `process_document` (and on
into `resolve` / fill). Planning class = `{"spec", "clarify", "plan", "tasks"}` (the speckit
specify/clarify/plan/tasks commands set exactly these labels at their `_stage_panel` call sites).
`paper_*` labels and a `None`/unknown label fall through to **full verification** (fail-safe toward
*more* verification, never less).

**Rationale**: The `stage_label` strings already exist at every command's `write_artifacts` hook
([clarify_cmd.py:235](../../src/llmxive/speckit/clarify_cmd.py#L235),
[plan_cmd.py:417](../../src/llmxive/speckit/plan_cmd.py#L417),
[tasks_cmd.py:602](../../src/llmxive/speckit/tasks_cmd.py#L602),
`paper_plan_cmd.py`, `paper_tasks_cmd.py`). They are the natural, already-present carrier of stage
identity — no new enum, no parallel concept. `process_document` is currently stage-blind
([slash_command.py:286](../../src/llmxive/speckit/slash_command.py#L286)); a single optional
parameter makes it stage-aware without disturbing existing callers (default `None` ⇒ today's
behavior).

**Alternatives considered**:
- *A global `LLMXIVE_PLANNING_STAGE` env var* (like the existing `LLMXIVE_CLAIM_LAYER`): rejected —
  the spec explicitly requires a signal "threaded to the claim layer (not a global, stage-blind
  setting)" (FR-001). A global env is exactly the stage-blind pattern to avoid, and would be wrong
  under concurrent multi-stage runs.
- *Re-use the `Stage` enum in [types.py:88](../../src/llmxive/types.py#L88)*: rejected — the enum
  encodes project *state* (`PLANNED`, `PAPER_PLANNED`, …), not the *artifact-producing command*; the
  `stage_label` string is the value actually available at the claim-layer call site.

---

## D2 — The strip/smooth transform (FR-002a, FR-002b)

**Decision**: New canonical module `claims/smooth.py::strip_and_smooth(passage, claim, *, backend,
model) -> str`. Pipeline: (1) **LLM rewrite** of the passage to a claim-free higher-level statement
that preserves intent and any citation, via `backends/router.py::reasoning_chat` (the centralized
reasoning entry point; 32K budget is ample for a one-passage rewrite); (2) **re-detect guard** —
re-run `claims/extract.py::extract_claims` (or the classify path) on the rewrite; if any low-level
claim with the same `subject_key` remains, (3) **deterministic fallback** — remove the asserting
clause/sentence span deterministically (no LLM), guaranteeing a claim-free result. The function
operates only on the low-level assertion; citations and surrounding non-claim text are preserved
(FR-002c).

**Rationale**: Matches clarification Q2 verbatim. The re-detect guard is what makes the transform
**idempotent** (FR-002b / SC-001a): the stored output is guaranteed to contain no detectable
low-level claim, so a later round's detector finds nothing to re-process and the passage is never
rewritten again — killing the planning-side waffling at the source. `reasoning_chat` is the single
resilience-policy entry point, so the rewrite inherits fallback/retry/breaker/deadline for free.

**Alternatives considered**:
- *Skip (don't verify) low-level claims, leave them in place*: rejected by the maintainer — leaves a
  possibly-false value unverified in the document.
- *Pure deterministic deletion (regex) only*: rejected — cannot smooth a load-bearing sentence into
  grammatical prose (edge case: "the strip/smooth would otherwise produce broken or empty prose").
  Used only as the **fallback** when the guard still detects a claim.
- *Replace with `[UNVERIFIED]` marker* (Principle II's escape hatch): rejected for planning — a
  marker is still a kickback-adjacent artifact and leaves the (now-flagged) value visible; the spec
  wants the specific value *gone*, generalized into a qualitative statement.

---

## D3 — Frozen, value-independent identity & immutability (FR-009, FR-010, FR-011)

**Decision**: Make `subject_key` the **primary reuse key** for freezing. Promote the existing
subject-key VERIFIED reuse ([service.py:186-207](../../src/llmxive/claims/service.py#L186-L207)) into
a first-class **frozen lookup**: before resolving any claim, look it up by `(kind, subject_key)` in
the `state/claims/` registry; if a VERIFIED record exists and its `source_hash` is unchanged, **adopt
its value with no re-resolution**. Guard the self-heal path
([service.py:94-107](../../src/llmxive/claims/service.py#L94-L107)) so it never re-resolves or
overwrites a record that is (or whose subject twin is) VERIFIED — a transient failure or a
pending re-extraction must not re-open a frozen fact (FR-011).

**Rationale**: `subject_key` already excludes the asserted/resolved value digits
([canonical.py:142-176](../../src/llmxive/claims/canonical.py#L142-L176)), so a rephrase/correction of
the same fact maps to the same record (FR-009). The registry is already git-tracked
([state/claims.py](../../src/llmxive/state/claims.py)), giving cross-run persistence (FR-013, SC-004)
without new storage. The only gaps are (a) reuse is currently keyed by text-hash `claim_id`
([service.py:92](../../src/llmxive/claims/service.py#L92)) so a rephrase misses, and (b) the
self-heal loop re-opens non-VERIFIED claims — both fixed by this decision.

**Alternatives considered**:
- *A new dedicated frozen-cache file*: rejected (FR-013 + Principle I) — `state/claims/` already
  exists, is git-tracked, and is keyed by claim records; adding a parallel store would duplicate it.
- *Freeze eternally (ignore source hash)*: rejected — edge case "a claim's cited source genuinely
  changes between runs" requires `source_hash`-keyed invalidation (FR-010, spec 016 FR-015).

---

## D4 — Durable placeholder + rendered view (FR-007, FR-008)

**Decision**: Split the rendering boundary. `claims/pointer.py::render(...)` produces the **canonical
stored form**, which carries a **durable placeholder token** for each verified claim (the
`{{claim:c_XXXXXXXX}}` pointer, kept — *not* baked into prose). `strip_claim_artifacts`
([extract.py:42-63](../../src/llmxive/claims/extract.py#L42-L63)) is changed to **preserve** these
durable pointers (it still removes `[UNRESOLVED-CLAIM:]` markers and stray/orphan pointers). A new
`render_view(text, registry) -> str` substitutes verified values from the **frozen store** for each
placeholder, deterministically, and is called only (a) at **review time** (the artifact handed to the
panel) and (b) for the **final published artifact**. Convergence operates on the placeholder
(canonical) form.

**Rationale**: Baking the value into prose ([pointer.py:168-207](../../src/llmxive/claims/pointer.py#L168-L207))
is the root cause of cross-round re-extraction: the literal value, once in prose, is re-detected as a
new claim next round (text-hash id differs ⇒ cache miss ⇒ re-resolve). A durable placeholder makes
the stored form non-re-extractable (SC-007) while `render_view` keeps the document human-readable and
reviewer-judgeable (FR-008). The substitution is deterministic (pure lookup from the frozen store),
so it never introduces waffling.

**Alternatives considered**:
- *Keep baking values, rely only on subject_key reuse to re-freeze*: rejected — even with perfect
  reuse, the baked literal is still re-extracted every round (wasted work, and any reuse miss
  re-opens it). The placeholder removes the re-extraction entirely (SC-007).
- *Store values out-of-band and strip them from prose with no placeholder*: rejected — loses the
  in-document anchor needed to render the value back deterministically at review/publish.

**Scope guard**: For planning stages the only verified claims are **citations**, whose canonical text
is the literal DOI/arXiv/URL (no value to substitute), so placeholders chiefly matter in the
paper/research stages with numeric/entity claims. The planning path's value comes from strip/smooth
(D2), not placeholders.

---

## D5 — Value-independent fill/verification cache key (FR-012)

**Decision**: Remove `claim.resolved_value` from the fill cache key
([fill/service.py:115-130](../../src/llmxive/fill/service.py#L115-L130) — `_cache_key_parts`
currently returns `("fill", fingerprint, claim.resolved_value)`), and make the fingerprint
value-excluded by keying on the `subject_key`-style identity rather than the all-numeric-tokens
`fact_fingerprint` ([subject_query.py:141-195](../../src/llmxive/fill/subject_query.py#L141-L195),
which captures **all** numeric tokens including the asserted value at L176-180). The grounding
verdict cache ([grounding/cache.py:71-80](../../src/llmxive/grounding/cache.py#L71-L80)) is keyed on
`(source_id, normalized_claim, number)`; `number` (the asserted value) is dropped from the key.

**Rationale**: With the asserted value in the key, a PENDING phrasing ("49") and the VERIFIED phrasing
("9,988") of the *same fact* compute different keys and miss each other — re-resolving every round.
Keying on the value-excluded subject identity makes both phrasings hit the same entry (FR-012),
reinforcing the freeze. Qualifier numbers (e.g. "at 13 crossings") stay in the identity because
`subject_key` keeps qualifier digits and only excludes the asserted/resolved value.

**Alternatives considered**:
- *Leave the grounding-cache as-is and rely on the registry freeze*: rejected — the grounding cache
  is consulted inside `fill_claim` before the registry freeze can short-circuit; a value-dependent
  key there still produces a cold miss and a redundant fetch. Both layers must be value-independent.

---

## D6 — Templates & prompts that invite low-level numbers (FR-006, US3)

**Decision**: Edit the producing guidance to state research-question + method + references and defer
specific empirical values to implementation, in all canonical locations and the per-project copies:
- [.specify/templates/spec-template.md](../../.specify/templates/spec-template.md) Success Criteria
  examples (L112-115: "1000 concurrent users", "90%", "Reduce … by 50%").
- [.specify/templates/plan-template.md](../../.specify/templates/plan-template.md) Technical Context
  (L26 Performance Goals "1000 req/s…", L28 Scale/Scope "10k users…").
- [.claude/skills/speckit-specify/SKILL.md](../../.claude/skills/speckit-specify/SKILL.md) Success
  Criteria Guidelines (L313-330); and the clarify/plan/tasks SKILL.md scope notes.
- [agents/prompts/panels/panel_plan_data_resources.md](../../agents/prompts/panels/panel_plan_data_resources.md).
- `projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/.specify/templates/{spec,plan}-template.md`
  (verified identical copies of the shared templates).

**Rationale**: Prevention (US3) reduces how often a low-level claim appears; the strip/smooth (US1) is
the cure for the ones that still slip through. Editing the per-project copies too is required by
FR-006 ("including … any per-project template copies") and Principle I (the copies are a known
duplication of the shared templates; until they are de-duplicated they must be kept in sync).

**Alternatives considered**:
- *Only edit the shared templates*: rejected — the per-project copies are what PROJ-552's commands
  actually read; leaving them stale would let low-level numbers keep appearing for that project.

---

## D7 — Testing strategy (FR-016)

**Decision**: Offline deterministic tests pin: stage gate (`is_planning_stage`), strip/smooth
idempotence (a smoothed passage re-detects zero low-level claims and is a no-op on re-run), frozen
subject_key lookup (no re-resolution; immutable on transient failure), value-independent cache key
(PENDING vs VERIFIED phrasings collide), durable-placeholder round-trip (stored form keeps the
placeholder; `render_view` substitutes). Real-call tests (`LLMXIVE_REAL_TESTS=1` + free Dartmouth
models) exercise: planning-skip (low-level numeric not fetched/grounded, no marker, no kickback),
planning reference-still-gated (fabricated DOI blocks), paper-stage no-regress (the 9,988 OEIS exact
count + a constant + an entity fact still verify + freeze), and the strip/smooth rewrite on real
prose.

**Rationale**: Principle III + FR-016 — deterministic logic is pinned offline for fast feedback; every
externally-dependent path has a real-call test as the primary signal. Must-not-regress suites:
`tests/unit/test_claim_*`, `test_fill_*`, `test_grounding_*`, `tests/integration/test_claim_subject_reuse.py`,
`test_exact_count_no_regress.py`, the convergence engine + reviser tests.
