# spec 026 Slice 7 — COMPLETE (handoff to Slice 8)

**Tracking** [#1285](https://github.com/ContextLab/llmXive/issues/1285) · **Branch**
`026-model-selection-consolidation` (91 commits ahead of `origin/main`, **NOT pushed**) ·
**Date** 2026-07-19

## State: Slice 7 done, gate green

|check|result|
|-|-|
|Manifest `owning_slice==7` rows|**0** (was 300)|
|Full non-slow suite|**7068 passed, 17 skipped, 0 failed**|
|Real-call vision|**2/2** against live Dartmouth|
|`git diff --check`|clean|
|Pushed?|**No** — rebase onto `origin/main` at PR time only|

> **This note originally declared completion PREMATURELY.** A maintainer review then
> found six defects, two of them blockers, all confirmed and since fixed (see
> "Review round 3" below). The zero-manifest-rows gate reported success while a whole
> subsystem was unmigrated. Treat a green automated gate as necessary, never sufficient.

## Review round 3 — six confirmed defects, all fixed

|#|severity|defect|fix|
|-|-|-|-|
|F1|**blocker**|`ImagePart` validated the caller's *declared* width/height but never checked them against the encoded bytes. A real 2000×2000 PNG declared 1×1 was accepted, so `TOKENS_PER_IMAGE` bounded nothing and FR-003's cost reservation was fiction.|`73f2562d65` — dimensions parsed canonically from PNG/JPEG/WebP headers (no new hard dep), `from_bytes` constructor, declared-vs-parsed mismatch rejected, plus mime/content, empty-payload and pixel-count checks|
|—|minor|F1's new `MAX_IMAGE_PIXELS = 2**21` made `TOKENS_PER_IMAGE`'s cited derivation (1536×1536 → 9 tiles) describe an input that can no longer exist|`2d057b53f3` — re-derived over ALL admissible shapes: max 9 tiles, reachable at 1025×1536 → 1615 ≤ 2048. Bound was always sound; only the documentation was wrong|
|F2|**blocker**|The convergence review panel — the platform's largest LLM consumer — was never migrated. 11 `reviewspecs.py` builders defaulted `model: str = DEFAULT_MODEL`; `llm_reviewer` stored `self._model`; cache keys used the pin.|`71715c2ad7` — `model` channel removed from all builders/wiring, `LLMReviewer` carries `profile="deep_review"`, cache identity keys on profile + `selection_policy_version`, plus a propagation test asserting at `route_chat` across the thread pool|
|F3|medium|`slash_command.py` still initialized `BackendName.DARTMOUTH` / `"unknown"`, fabricating a backend never contacted on the pre-response failure path|`c19c4c80ce` — nullable locals matching `agents/base.py`, tests at three distinct failure points|
|F4|medium|AC4 recreated a hardcoded family allowlist under a new name, and the capability policy records *competence*, not cost|`2c5af124d6` — free/paid asserted from snapshot `Candidate.pricing.is_free`; unknown-priced never free; absent families never resurrected|
|F5|medium|"Exact projections" asserted only `ids[:3]` plus membership — extra candidates, wrong ordering or duplicates would pass|`fc9c370d30` — complete ordered tuples per profile under paid-off and paid-on|
|F6|low|`spec.md` still said "no other quality-bar change" immediately before documenting a new one; plan EOF whitespace|`e21d314f09` — all four sanctioned deltas enumerated|

**Why the automated gate missed F2 — the transferable lesson.** The migration manifest scans for
model-id string *literals*. `DEFAULT_MODEL` is a *symbol reference*, so the scan saw nothing while an
entire subsystem stayed on the provisional profile. The Slice-7 design (§5.1) explicitly predicted
this — "the manifest finds literals; it cannot see an interface that merely permits a pin" — and the
gate was trusted anyway. **Grep for the symbols, not just the literals.** F2 also blocked Slice 8,
which cannot delete `DEFAULT_MODEL` while anything imports it (nothing does now — verified).

**Why my own F1 verification missed it.** I empirically checked that the token bound computed
correctly using *honest* dimensions, which confirmed the arithmetic while never testing the trust
boundary. Verifying that a bound is *computed* right is not verifying that it cannot be *evaded*.

Design: [2026-07-19-issue-1242-slice7-design.md](2026-07-19-issue-1242-slice7-design.md) (rev 3).
Plan: [2026-07-19-spec-026-slice7-plan.md](2026-07-19-spec-026-slice7-plan.md).
Ledger: `.superpowers/sdd/progress.md` (git-ignored).

## Commits (14)

`0aa67ebb0d`+`caf241203e` exclude_leader · `3aa1058ab1` no-llm bypass · `653924881d` multimodal ·
`c26255602a` vision policy v2 + figure migration · `3a6dd49a0d` registry profile schema ·
`a12f6b5a10` 43 direct pins · `05533ed132` summarize budgets · `db17d8dcac` run-log nullable ·
`cc203c2450` US5 AC1+AC4 · `6f17410cbb` spec deltas · `b67fdb1a9b` evidence-citation fix ·
`eaa036d551` slice-8 reassign + final gate

## The 7 binding constraints — all verified directly (not from subagent reports)

1. **Behavior preserved** — AC1 test: all 53 LLM agents lead `qwen.qwen3.5-122b` under the fixed
   snapshot; re-confirmed on a composite snapshot. gemma-4 retained.
2. **`select()` purity** — `exclude_leader` is a two-pass translation in `route_chat`; the returned
   chain is still the direct output of `select(requirement, snapshot)`. A discriminating test
   distinguishes merged-requirement from base-only leader resolution.
3. **FR-010 disposition** — `UnsupportedFeatureError` → SKIP, checked before its
   `PermanentBackendError` base (`router.py:205-213`), mirroring `PaidGuardDenied`.
4. **FR-003 cost bound** — verified empirically: 5 images in one message price ≥ 5×`TOKENS_PER_IMAGE`;
   5 separate messages likewise; `dataclasses.replace` re-runs validation; oversize rejected;
   str path byte-identical (4028 == 4028).
5. **No stray model-id literals** — independent grep; the only remainder is `router.py`'s
   `MODEL_FALLBACKS`, which is **Slice 8's** deletion target.
6. **Audit safety** — inspection tests assert image metadata present AND raw/base64 bytes absent.
7. **`paid_opt_in` does not gate the paid tail** — all 53 agents have it `False`, yet every profile
   yields the guarded paid tail under process opt-in with headroom; free-only when opt-in is off.

## SLICE 8 — what's next (LAST, irreversible, gate on full green)

1. **`model_selection/enforcement.py`** + a static test consuming the manifest JSON: no production
   model-id literal outside the canonical layer (`policy.py` + the live catalog). Fixtures/tests
   allowed. The manifest now labels the single remaining target `owning_slice: 8`.
2. **Only after full green, DELETE:**
   - `backends/router.py` `MODEL_FALLBACKS`, `DEFAULT_MODEL`, `PAID_FALLBACK_MODELS`
   - `backends/dartmouth.py` `KNOWN_FREE_MODELS` (**the sole `owning_slice==8` manifest row**)
   - `state/execution_status.py` `_LEGACY_PAID_TIERS_ENV` + its `_LEGACY_WARNED` latch
   - residual private pin tables
   **DO NOT delete** `dartmouth.py` `_REASONING_MODELS` — canonical (serving-mode knowledge).
3. `test_config_consistency` was already re-pointed at capability profiles in Slice 7, so it will
   not break when the allowlists go.

## Gotchas the next session will hit

- **Regenerate the manifest after ANY file change** — line-number drift fails
  `test_committed_manifest_is_current_with_the_live_scan`. This cost three extra full-suite runs.
- **The full suite takes ~5-6 min** — a 2-minute Bash timeout kills it mid-run.
- **7 RUF001 lint reports are DELIBERATE.** Those non-breaking hyphens live inside regex character
  classes that intentionally match what LLMs emit (`_REQ_ID_RE = r"\b((?:FR|SC)[-‑]?\d{1,3}[a-z]?)\b"`,
  with a matching `raw.replace("‑", "-")` normalizer). "Fixing" them breaks FR/SC id matching. They
  are pre-existing — zero occurrences in Slice 7's diff. ~40 further ruff errors elsewhere in the
  repo are pre-existing and out of scope.
- **Subagent final messages were unreliable this session** — 8+ returned empty or bare "DONE"
  despite explicit contracts, while having done the work. Verify every task from `git log`, the
  report files under `.superpowers/sdd/`, and your own test runs. Resume a silent agent with
  `SendMessage` rather than re-dispatching (it keeps its context).

## Plan defects found during execution (for future plan-writing)

- **T5 and T6 were never separable.** Deleting a schema field cannot be committed green without
  simultaneously updating all 91 consumers, so T6 was absorbed. Decompose by *commit atomicity*,
  not by conceptual grouping.
- **T4's gate test was circular** — it asserted `route_chat(profile="vision")` returns qwen3.5, but
  `select()` could not route vision to qwen3.5 until the very policy change the gate was gating. The
  gate had to be run directly against the backend. Check that a gate can actually execute *before*
  the step it guards.
- **T2's Step 4 sketched a dispatch function that does not exist** (`_run_deterministic_agent`);
  `paper_publisher` is dispatched by name via `_NON_SPECKIT_AGENTS` to a subclass whose `run()`
  never enters the LLM layer.
- **My own first draft mandated a non-strict `xfail` and two `pytest.raises(Exception)` catch-alls** —
  tests that cannot fail. Caught in pre-flight, before any dispatch.
