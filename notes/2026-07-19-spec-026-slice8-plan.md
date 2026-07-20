# spec 026 Slice 8 — static enforcement + deletion (LAST, irreversible)

**Tracking** [#1285](https://github.com/ContextLab/llmXive/issues/1285) · **Branch**
`026-model-selection-consolidation` (not pushed) · **Date** 2026-07-19 ·
**Predecessor** [Slice-7 handoff](2026-07-19-spec-026-slice7-handoff.md)

Slice 7 left exactly ONE `owning_slice==8` manifest row (`dartmouth.KNOWN_FREE_MODELS`) and
verified that **nothing imports `DEFAULT_MODEL`** any more. This slice adds the static guard, then
performs the irreversible deletions behind it.

## Order is load-bearing

Enforcement lands FIRST, then the deletions — so the guard that prevents pins returning is in place
before the pins go, and a regression is caught by a test rather than by absence.

## Maintainer decision (2026-07-19)

**`KNOWN_FREE_MODELS` is deleted, but only after `is_free_model` gains an LKG-backed fallback.**

It is NOT the same kind of symbol as the other three targets. `MODEL_FALLBACKS` / `DEFAULT_MODEL` /
`PAID_FALLBACK_MODELS` are **selection** pins whose consumers Slice 7 removed. `KNOWN_FREE_MODELS` is
a **cost-safety outage fallback** with a LIVE consumer: `dartmouth.is_free_model()` (`:663-673`)
falls back to it when `free_chat_models()` returns `None`, and `dartmouth.chat()` uses the result to
decide whether the paid guard applies (`paid_call = not is_free_model(model)`).

Deleting it bare would mean: catalog listing blip → every free model reads as paid → with
`LLMXIVE_PAID_OPT_IN` OFF (the default) the guard raises `PaidGuardDenied` → every candidate is
SKIPPED → `ChainExhausted` → **platform-wide LLM outage while the models themselves are up and free.**

The spec anticipated the right answer: live-catalog pricing **+ the LKG store** supersede the
allowlist. LKG pricing is a REAL timestamped observation, not "unknown", so it satisfies SC-003
("unknown cost is never free") while preserving availability.

## Tasks

### S8-T1 — `enforcement.py` + static test (BEFORE any deletion)
- `src/llmxive/model_selection/enforcement.py`: scan production code (`src/llmxive/**`) for model-id
  literals outside the **canonical layer**. Consume `migration_manifest.json` — do not re-implement
  detection; reuse `inventory.py`'s `looks_like_model_id` / scanning so the two cannot disagree
  (Constitution I).
- Canonical/allowed: `model_selection/policy.py`, the live catalog layer, `dartmouth._REASONING_MODELS`
  (serving-mode knowledge), `backends/local.py:list_models` (the backend declaring its own inventory,
  SC-010), plus `tests/**`, fixtures, and the manifest itself.
- Test asserts ZERO unsanctioned production pins. It must FAIL if a pin is reintroduced — prove that
  with a fixture containing a planted pin, not merely by passing on the current tree.
- **The scan must catch SYMBOL REFERENCES, not just literals.** The Slice-7 gate reported zero rows
  while `reviewspecs.py` imported `DEFAULT_MODEL`; a literal-only scan is what let that through.

### S8-T2 — LKG-backed `is_free_model`, then delete `KNOWN_FREE_MODELS`
```python
def is_free_model(model: str) -> bool:
    live = free_chat_models()
    if live is not None:
        return model in live          # authoritative live pricing
    lkg = _lkg_free_models()          # aged but REAL observation
    if lkg is not None:
        return model in lkg
    return False                      # genuinely unknown -> never free (SC-003)
```
- `_lkg_free_models()` reads the catalog component's persisted pricing via the LKG store, using a
  **function-local import** of `model_selection` (`backends` must not import it at module scope —
  the cycle guarded all through Slice 7; `ImagePart.__post_init__` is the precedent).
- Any LKG read failure → `None` → fail closed. The LKG path must never raise into the call path.
- Tests: live-hit; catalog-outage-with-LKG (free preserved); catalog-outage-without-LKG (fails closed
  to paid); LKG corrupt/absent → treated as absent; and a test proving a catalog blip no longer
  denies a known-free model.
- THEN delete `KNOWN_FREE_MODELS` + its `__all__` entry.

### S8-T3 — delete the selection pins
- `backends/router.py`: `MODEL_FALLBACKS` (:58), `DEFAULT_MODEL` (:99), `PAID_FALLBACK_MODELS` (:105)
- `state/execution_status.py`: `_LEGACY_PAID_TIERS_ENV` (:73) + the `_LEGACY_WARNED` latch (:76) and
  its one-time-warning branch — the deprecated `LLMXIVE_EXECUTION_PAID_TIERS` bridge Slice 6 left.
- **DO NOT delete `dartmouth._REASONING_MODELS`** — canonical (thinking-mode disable + reasoning-safe
  budget), explicitly not a migration target.
- Update every consumer, including the test files that import these symbols
  (`test_chat_with_fallback_delegation`, `test_config_consistency`, `test_reasoning_walker_delegation`,
  `test_model_selection_inventory`, `test_model_selection_select`, `test_execution_tier_constraints`,
  `test_execution_exhaustion_flow`). Prose references in docstrings that describe the retired design
  are fine to keep if reworded to past tense.

### S8-T4 — final gate
- Regenerate the manifest; assert ZERO `owning_slice==7` AND ZERO `owning_slice==8` rows.
- Full non-slow suite green; ruff clean on changed files; `git diff --check` clean.
- Real-call sanity: `LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_vision_real.py` (the
  `is_free_model` change touches the paid-guard path every real call crosses).
- **Do NOT push.**

## Constraints (inherited)

Commit each task with `PRE_COMMIT_ALLOW_NO_CONFIG=1` + the `Co-Authored-By` trailer; verify HEAD
moved. Real tests, no mocks as the primary path. Keep the autouse `_offline_model_selection_snapshot`
fixture. Fix the CODE when a test fails — never weaken a test. 7 RUF001 reports in
`types.py`/`engine.py`/`implementer.py` are DELIBERATE (intentional non-breaking hyphens inside regex
character classes) — leave them.

## Definition of done

`enforcement.py` green and proven to fail on a planted pin; `MODEL_FALLBACKS` / `DEFAULT_MODEL` /
`PAID_FALLBACK_MODELS` / `KNOWN_FREE_MODELS` / the legacy paid-tiers shim all gone; `is_free_model`
LKG-backed and fail-closed; zero slice-7 and slice-8 manifest rows; full suite green. Then spec 026
is complete and the branch is ready for the slices 0–8 review.
