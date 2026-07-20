# spec 026 — COMPLETE (slices 0–8), ready for whole-spec review

**Tracking** [#1285](https://github.com/ContextLab/llmXive/issues/1285) · **Branch**
`026-model-selection-consolidation` — 111 commits ahead of `origin/main`, **NOT pushed** ·
**Date** 2026-07-19

## Final gate

|check|result|
|-|-|
|Full non-slow suite|**7098 passed, 17 skipped, 0 failed**|
|Manifest migration rows|**0** — only `canonical_layer` (8) + `test_double` (294) remain|
|`enforcement.py` guard|9 passed, still green AFTER the deletions|
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

Verified empirically: outage **with** LKG keeps `qwen.qwen3.5-122b` free (platform stays up); outage
**without** LKG returns False (SC-003 honored). `backends` reaches `model_selection` through a
function-local import — the cycle guarded all through spec 026.

**T3 — selection-pin deletion (`cfa8dbfc1e`).** The three router tables plus the legacy paid-tiers
shim and its `_LEGACY_WARNED` latch. `LLMXIVE_EXECUTION_PAID_ESCALATION` (the boolean) stays.

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
