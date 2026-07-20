# spec 026 — COMPLETE (slices 0–8), ready for whole-spec review

**Tracking** [#1285](https://github.com/ContextLab/llmXive/issues/1285) · **Branch**
`026-model-selection-consolidation` — 115 commits ahead of `origin/main`, **NOT pushed** ·
**Date** 2026-07-19

## Final gate

|check|result|
|-|-|
|Full non-slow suite|**7108 passed, 17 skipped, 0 failed**|
|Manifest migration rows|**0** — only `canonical_layer` (8) + `test_double` (292) remain|
|`enforcement.py` guard|12 passed, green AFTER the deletions AND after the round-5 hardening|
|Real calls|vision 2/2 + dartmouth chat, live|
|ruff (slice-8 files) / `git diff --check`|clean|

`DEFAULT_MODEL`, `MODEL_FALLBACKS`, `PAID_FALLBACK_MODELS`, `KNOWN_FREE_MODELS` and the legacy
`LLMXIVE_EXECUTION_PAID_TIERS` shim are all **deleted**. `dartmouth._REASONING_MODELS` is retained —
canonical serving-mode knowledge, never a migration target.

## Slice 8, as built

**T1 — `model_selection/enforcement.py` (`c3fb7be315`).** Static guard, landed BEFORE any deletion so
the thing preventing pins from returning existed before the pins went. It reuses `inventory.py`'s
detector (one detector, Constitution I) and — critically — flags **retired symbol references, not
just string literals**. That is a direct response to the Slice-7 failure where a literal-only gate
reported "zero rows" while `reviewspecs.py` imported `DEFAULT_MODEL` and 11 builders defaulted to it.
The guard is name-based, so it keeps working now that the symbols are gone. Planted-violation tests
prove it detects both a literal pin and a symbol import rather than merely passing on a clean tree.

**T2 — LKG-backed `is_free_model` (`9b501e7a68`).** The one scope change in this slice, and the only
place where "delete the pin" would have been actively harmful. `KNOWN_FREE_MODELS` was not a
selection pin; it was a cost-safety outage fallback with a live consumer. `dartmouth.chat()` does
`paid_call = not is_free_model(model)`, so deleting the fallback bare would mean: catalog listing
blip → every free model reads as paid → with opt-in OFF (the default) the credit guard denies every
candidate → chains exhaust → **platform-wide LLM outage while the models are up and free.**

Replaced with the ladder the spec anticipated (live pricing **+ LKG** supersede the allowlist):

```
live catalog        -> authoritative
  |
  v (outage)
LKG catalog pricing -> aged but a REAL timestamped observation, not "unknown"
  |
  v (cold start, no LKG)
False               -> fail closed; unknown cost is never free (SC-003)
```

Verified empirically: outage **with a FRESH LKG** keeps `qwen.qwen3.5-122b` free (platform stays up);
outage without LKG — or with one older than the freshness bound — returns False (SC-003 honored).
`backends` reaches `model_selection` through a function-local import — the cycle guarded all through
spec 026. **Note the qualifier**: as first built this ladder had NO age bound at all, which review
round 5 correctly flagged as a spend-authorization hole; see R2 below and the open judgment call.

**T3 — selection-pin deletion (`cfa8dbfc1e`).** The three router tables plus the legacy paid-tiers
shim and its `_LEGACY_WARNED` latch. `LLMXIVE_EXECUTION_PAID_ESCALATION` (the boolean) stays.

## Review round 5 — two Slice-8 defects, both in what the author specified

|#|severity|defect|fix|
|-|-|-|-|
|R1|**blocker**|`enforcement.py` treated every `migration_target` row already in the GENERATED manifest as sanctioned. Since the documented workflow regenerates the manifest after every pin move, the guard was CIRCULAR: add a pin → regenerate → the pin becomes its own permission slip. Reproduced: 1 violation before regen, **0** after. Second hole: `_RETIRED_SYMBOL_OWNER_FILES` permanently exempted `router.py`/`dartmouth.py` from retired-symbol scanning, so `DEFAULT_MODEL = _choose_at_runtime()` in the former owner file was invisible.|`fbf3a5fc12` — manifest baseline DELETED (sanction now comes only from `inventory.py`'s hand-maintained `_CANONICAL_FILES`/`_CANONICAL_SYMBOLS`, a reviewed code allowlist); owner-file exemption removed; `Store` contexts (assignments) detected, not just imports/`Load`. Re-verified by the original probes: planted pin now survives regeneration (1 → 1), owner-file redefinition caught.|
|R2|high|The free/paid ladder had NO freshness bound on either source: `_FREE_MODELS_CACHE` was process-lifetime with no timestamp, and `_lkg_free_models` ignored `LKGEntry.observed_at` entirely. A stale "free" verdict bypasses `paid_call_allowed()` — this sits directly on the spend-authorization boundary (FR-007, SC-003).|`c3900d0992` — monotonic TTL on the in-process cache (refetch failure falls through to LKG rather than serving an expired cache); LKG entries older than the bound rejected → fail closed; tz-naive/aware both handled without raising.|

**The lesson from R1.** My dispatch said "consume `migration_manifest.json` for the sanctioned classifications." That single instruction made a *generated* artifact the authority on what is permitted — and a guard whose baseline regenerates alongside the thing it guards is not a guard. Sanction must come from a reviewed, hand-maintained allowlist in code. The manifest is now read for reporting only and cannot suppress a violation.

**The lesson from R2.** The Slice-8 plan called LKG pricing "aged but a REAL timestamped observation" — and then never looked at the timestamp. Naming a property is not enforcing it.

## OPEN JUDGMENT CALL for the 0–8 review: the freshness bound conflates two volatilities

The R2 fix derives its bound from `PROFILES["independent_review"].max_catalog_age_s` = **900s**, per
Constitution I (derive, don't duplicate). That is defensible but semantically imprecise, and the
consequence is real:

- `max_catalog_age_s=900` exists in the SELECTION layer because model **availability/health** changes
  fast — a high-stakes call wants a fresh view of *what is up*.
- The paid guard needs a fresh view of **pricing**, which changes rarely (a free→paid transition is an
  infrequent, announced event).

Because LKG only refreshes on a SUCCESSFUL live fetch, it ages monotonically during an outage. So the
ladder now protects roughly **15 minutes** of catalog outage; past that, every free model reads as
paid, the guard denies, and chains exhaust — the exact failure mode the LKG ladder was built to
prevent. Verified live: the current on-disk LKG (10.9 h old) is rejected, so `is_free_model` returns
False during a simulated outage.

**Author's recommendation: KEEP 900s**, but record it as a deliberate decision rather than a
side-effect of constant reuse. Failing closed is the right posture for an autonomous system that
spends money: a longer pricing-specific bound (say 24 h) would preserve availability but expose up to
24 h of *unmetered* spend if a model went free→paid, because the credit guard would never engage. The
cost of failing closed is proportionate — the pipeline skips cron ticks during an infrastructure
outage and retries; nothing user-facing is down. If the reviewer prefers availability over that
posture, the change is one constant plus its tests.

## For the slices 0–8 review

**Where the defects clustered.** Every blocker found across four Slice-7 review rounds was a **trust
boundary** or a **completeness gap**, never a logic error:

|defect|shape|
|-|-|
|`ImagePart` believed caller-declared dimensions|trusted unverified input|
|review cache key omitted `RequirementOverrides`|hand-listed key, silently incomplete|
|convergence panel never migrated|literal-scanning gate blind to symbol references|
|PNG accepted a zero-length IHDR|structural validation weaker than its documentation claimed|

Three recurred as a single theme: **a green automated gate is necessary and never sufficient.** The
manifest gate reported zero rows with a whole subsystem unmigrated; the test suite was fully green
with escalation silently no-oped; my own empirical bound check passed because I used honest inputs.

**Highest-value places to look in review:** `backends/base.py` (image trust boundary),
`convergence/review_cache.py` + `llm_reviewer.py` (key completeness), `backends/dartmouth.py`
`is_free_model` (the new outage ladder — cost-safety vs availability), and
`model_selection/enforcement.py` (does the guard actually catch what it claims?).

**Not independently reviewed.** No automated independent review completed: 11 subagent invocations
returned degenerate non-answers (`"Idle."`, `"No action remaining."`, bare `"DONE"`) after doing real
work, and Codex cross-validation is unavailable on this account (`gpt-5.2` / `gpt-5.3-codex` both
rejected for ChatGPT-account Codex). Every verification recorded here is the author's own. Given that
two blockers slipped past exactly that kind of self-verification, the built-in `/code-review ultra`
(cloud, billed, user-triggered) is worth running before the PR.

**Deliberate non-fixes.** 7 RUF001 "ambiguous unicode hyphen" lint reports in `types.py`,
`convergence/engine.py`, `agents/implementer.py`: those characters sit inside regex character classes
that intentionally match the non-breaking hyphen LLMs emit (`_REQ_ID_RE = r"\b((?:FR|SC)[-‑]?\d{1,3}[a-z]?)\b"`,
with a matching `raw.replace("‑", "-")` normalizer). "Fixing" them breaks FR/SC id matching. They are
pre-existing — zero occurrences in this branch's diff.

**Open, minor:** an EXIF-rotated JPEG's displayed dimensions differ from its encoded ones. Harmless
for the cost bound (pixel count is rotation-invariant), but `ImagePart.width/height` would disagree
with what a provider renders if anything downstream ever reasons about aspect ratio.

## PR prep

Rebase onto `origin/main` at PR time only — local `main` lags ~785 commits and the pipeline crons
commit constantly. Nothing in this branch has been pushed.
