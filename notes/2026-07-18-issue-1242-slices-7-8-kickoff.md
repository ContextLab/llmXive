# Issue #1242 / spec 026 — Slices 7 & 8 KICKOFF (fresh-session start guide)

**You are picking up spec-026 model-selection consolidation after Slice 6 landed.** Branch
`026-model-selection-consolidation` (do NOT push; re-fetch + **rebase onto origin/main first** — local
main lags ~785 commits, pipeline crons commit constantly). Slice 6 completion + verification is in
[2026-07-18-issue-1242-slice6-handoff.md](2026-07-18-issue-1242-slice6-handoff.md). This note is the
kickoff for the two REMAINING slices. Slices 1–6 are done, green, and reviewed.

## Read these FIRST (authoritative — do not re-derive; this note only adds operational context)
- **`specs/026-model-selection-consolidation/spec.md`** — US5 "Delivery split" (the deferred ACs you
  must land), US7, FR-012 (the 6 named profiles), FR-013 (all pins resolve through the mechanism),
  SC-007 (golden projections), and the require_paid/tier-ladder deltas Slice 6 recorded.
- **`specs/026-model-selection-consolidation/plan.md`** — the Slice 7 and Slice 8 paragraphs (the
  canonical scope; quoted-in-brief below).
- **`specs/026-model-selection-consolidation/migration_manifest.{md,json}`** — THE WORK-LIST. It is a
  frozen, drift-tested scan of every model-id pin in the repo. Filter `migration_target` entries by
  `owning_slice`: **Slice 7 = 136 rows** (each is a `file:line`, `kind`, `symbol` to migrate), Slice 5
  = 3 (done, will drop when their symbols delete in Slice 8). Regenerate after EVERY pin move:
  `.venv/bin/python -m llmxive.model_selection.inventory` (writes json+md; `test_model_selection_inventory`
  frozen-drift test enforces they match the live scan).
- **The Slice-6 design + plan** ([2026-07-18-issue-1242-slice6-{design,plan}.md](2026-07-18-issue-1242-slice6-design.md))
  — the patterns you'll reuse: the TYPE_CHECKING import discipline, the compose-merge, the SDD workflow.

## Mechanism as-built (what the remaining pins migrate ONTO)
`route_chat` (`model_selection/route.py`) is the single chokepoint: acquire snapshot → `build_requirement(profile, …)` → pure `select()` → `execute()`. Call sites express a **named profile**, never a model id. The 6 profiles live in **`model_selection/profiles.py`** (`cheap_structured`, `standard_generation`, `deep_review`, `deep_code`, `vision`, `independent_review`). Registry agents currently route through a **provisional `standard_generation`** profile (Slice 5) regardless of their real intent — Slice 7 makes each pick its true profile. `RequirementOverrides` (escalation) composes on top. Paid is gated by opt-in + `credits.fresh_paid_headroom_available` + per-call ceiling + the git ledger.

## SLICE 7 — compatibility consumers + `AgentRegistryEntry` schema migration
Plan.md: *"Migrate `types.py` (AgentRegistryEntry fields default_model/default_backend/fallback_backends → capability profile, with a schema migration for persisted execution state that carries model_tier), CLI/web/run-log/paper_reprocess/librarian, the reasoning_chat/chat_with_model_fallback direct-pin consumers (claims/fill/grounding/convergence — currently on provisional standard_generation), and test doubles — each behavior-preserving against the fixed migration snapshot. Also lands US5's deferred schema-dependent acceptance (BINDING): each agent expresses its own requirement profile; the all-LLM-agents fixed-migration-snapshot primary-preservation test (US5 AC1); and test_config_consistency validating capability profiles instead of the KNOWN_FREE_MODELS/MODEL_FALLBACKS allowlists (US5 AC4)."*

**Concrete scope + first steps:**
1. **The registry-entry schema.** Today `agents/registry.yaml` entries carry raw `default_model` /
   `default_backend` / `fallback_backends`, consumed as `field_consumer` rows across `agents/*.py`
   (`base.py`, `implementer.py`, `librarian.py`, `grounding_guard.py`, `paper_reviewer.py`,
   `task_verifier.py`, …). Locate the entry dataclass (grep `default_model:` in `agents/`; it's loaded
   from `registry.yaml`). Add a **capability-`profile`** field per agent (one of the 6), migrate the
   consumers to resolve via `select()`/`route_chat(profile=…)` with the agent's own profile instead of
   the provisional `standard_generation`. Behavior-preserving against the fixed migration snapshot.
2. **Persisted-state schema migration:** the registry-schema change must PRESERVE `execution_status`'s
   persisted `model_tier` (and the other counters) — write the migration so in-flight projects keep
   their tier. (Slice 6's `model_tier` state machine is stable; don't churn it.)
3. **Direct-pin reasoning consumers** now on provisional `standard_generation`: claims / fill /
   grounding / convergence callers of `reasoning_chat` / `chat_with_model_fallback` → their REAL
   profiles (e.g. `deep_review` for review lenses, `cheap_structured` for extraction).
4. **US5 deferred ACs (BINDING):** **AC1** an all-LLM-agents fixed-migration-snapshot primary-preservation
   test (every agent's chain leader matches the legacy default under the frozen snapshot); **AC4**
   rewrite `tests/unit/test_config_consistency.py` (`test_registry_models_are_free_unless_paid_opt_in`
   :59, `test_model_fallback_chains_are_free` :77) to validate **capability profiles**, NOT the
   `KNOWN_FREE_MODELS` (`backends/dartmouth.py`) / `MODEL_FALLBACKS` allowlists.
5. **Work-list:** the 136 `owning_slice==7` manifest rows. Regenerate the manifest after each pin move.

**Gotchas:** import cycle — import `model_selection` types into `backends`/`agents` under `TYPE_CHECKING`
+ `from __future__ import annotations` (string annotations); if you touch `agents/prompts/**` the
promptfoo eval gate fires (Slice 7 is schema, so probably N/A — keep it that way); `qwen.qwen3.5-122b`
stays the default; gemma-4 stays (approved). Every touched file must keep the offline suite green.

## SLICE 8 — static enforcement + deletion (LAST; irreversible; gated on FULL green)
Plan.md: *"`enforcement.py` scans against the manifest (no unsanctioned production pins outside the
canonical layer; fixtures/tests allowed); gated on the full suite being green, then delete DEFAULT_MODEL
+ MODEL_FALLBACKS and the residual private tables."*

**Concrete scope:**
1. Add `model_selection/enforcement.py` + a static test: scan production code for model-id literals
   outside the **canonical layer** (`model_selection/policy.py` + the live catalog); fixtures/tests/the
   manifest itself are allowed. This consumes the manifest json.
2. **Only after the full non-slow suite is green**, DELETE (exact current locations):
   - `backends/router.py:56` `MODEL_FALLBACKS`, `:97` `DEFAULT_MODEL`, `:103` `PAID_FALLBACK_MODELS`
   - `backends/dartmouth.py` `KNOWN_FREE_MODELS` (the migration_target allowlist)
   - `state/execution_status.py:72` `_LEGACY_PAID_TIERS_ENV` (the deprecated `LLMXIVE_EXECUTION_PAID_TIERS`
     shim — Slice 6 left it as a one-time-warning bridge; Slice 8 removes it + the `_LEGACY_WARNED` latch)
   - residual private pin tables.
   **DO NOT delete** `dartmouth.py:86` `_REASONING_MODELS` — M0 decision-A marked it **canonical**
   (backend serving-mode knowledge: thinking-mode disable + reasoning-safe budget), NOT a migration target.
3. Update every consumer of the deleted symbols (test_config_consistency was already re-pointed in
   Slice 7); the enforcement test then guards against regressions.

## Workflow / conventions (all slices)
- Every commit: `PRE_COMMIT_ALLOW_NO_CONFIG=1 git commit …` + trailer
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved; NO push.
- Constitution III: real tests, no mocks as the primary path; the autouse `_offline_model_selection_snapshot`
  conftest fixture makes routing deterministic offline (don't remove it).
- No model-id literals outside the canonical policy/catalog layer (that's the whole spec).
- Regenerate the manifest after every pin move (frozen-drift test).
- **Recommended approach:** Slice 7's schema migration is non-trivial (persisted-state migration + 136
  rows + 2 binding ACs) — run brainstorm → writing-plans → subagent-driven-development, exactly as Slice 6
  did (that flow worked well; per-task implementer + spec/quality reviewer + an opus final review). Slice
  8 is smaller but irreversible — plan it, gate the deletions on a full-green run, and do the enforcement
  test BEFORE the deletions. SDD scratch artifacts from Slice 6 are under `.superpowers/sdd/` (git-ignored).

## Definition of done (spec 026 complete)
All `migration_target` rows resolved; `DEFAULT_MODEL`/`MODEL_FALLBACKS`/`PAID_FALLBACK_MODELS`/
`KNOWN_FREE_MODELS`/the legacy paid-tiers shim deleted; `enforcement.py` green; `test_config_consistency`
validates profiles; US5 AC1+AC4 landed; full non-slow suite green; SC-008 real-call verified (needs
`DARTMOUTH_CHAT_API_KEY`). Then rebase onto origin/main → PR.
