# Issue #294 audit remediation — engineering note (2026-06-10)

Spec: `specs/021-project-audit-remediation/`. Branch:
`claude/zealous-gates-e5pv8o`. This note records what the audit got
right/wrong against the live repo, the root causes fixed, and the
real-call validation evidence (Constitution III).

## Audit claims vs verified reality

| #294 claim | Verified state | Action |
|---|---|---|
| Stale `pipeline_config.yaml` (paid models + score gates) | Real, but **orphaned** — consumed only by `scripts/pipeline_api.py` / `pipeline_config_manager.py` / `configurable_pipeline_orchestrator.py`, none reachable from live code or workflows | Deleted, with the whole legacy island (see below) |
| README still says "points threshold" | **Already fixed** in README — but the abolished text was still being *generated into the public site* by `web_data.py:259,281` ("points threshold", "Human reviews count double"), plus a stale `advancement.py` docstring | Fixed at the source; `projects.json` regenerated |
| README "Gemma 3 27B" vs registry `google.gemma-4-31B-it` | Real. Run-log evidence: `gemma-4-31B-it` is served live (5 calls 2026-06-05..08); registry + `MODEL_FALLBACKS` agree | Prose reconciled to the registry; guard test pins it |
| #112 judge non-determinism | Real: no temperature pinned; docstring-claimed verdict cache did not exist | Fixed (see below) |
| #256 claim layer missing | **Superseded**: specs 016–020 fully implemented (claims register→resolve→cache, receipts, triples, semantic substantiation) | Validated with real calls; issue closed with mapping |
| Validation gaps at the LLM boundary | Real, with live evidence: every recent `gemma-4-31B-it` reviewer fallback call died fatally on "response missing YAML frontmatter" | Bounded retry-with-feedback added at `Agent.run` |
| Adopt Pydantic + Instructor | Pydantic already pervasive (`types.py`); **Instructor rejected deliberately** — it would bypass the router's free-model guard, circuit breakers, and peer-model fallback. Same pattern (validation error fed back, bounded retries) implemented inside the boundary | `MalformedResponseError` + retry loop |

## Legacy island removed (Constitution I)

Zero-reference sweep (sub-agent) before deletion; "live" references to
`src/core/*.js` / `code_execution_manager.py` were circular within the
island itself. Removed: `pipeline_config.yaml`, `pipeline_schema.json`,
root `package.json`/lockfile (deps served only `validate-structure.js`),
`src/core/` (incl. `review_points_threshold: 5`), 10 `scripts/*.js`,
the configurable-pipeline scripts, `prompts/`, `system_prompts/`, and the
root-level legacy test island (`tests/test_code_execution_manager.py` et
al., `tests/run_tests.py`). CI runs only `tests/contract` +
`tests/real_call` (+ unit/integration locally), so nothing CI-visible
changed.

## #112 fix details

Root causes (both confirmed in code): no `temperature` passed by
`judge_one()`, and no verdict cache despite the docstring's claim.
Fix: `JUDGE_TEMPERATURE = 0.0`; frozen per-verdict cache at
`state/librarian-cache/judge/<sha256>.json` keyed by
`(normalize_term(query), candidate primary_pointer, JUDGE_PROMPT_VERSION)`
where `JUDGE_PROMPT_VERSION` is a content hash of the system prompt
(rubric edits auto-invalidate by changing the key). Fail-open verdicts
are never cached, so a transient outage cannot latch into a permanent
admit. The local backend's `temperature or 0.7` falsy-zero bug was fixed
in the same pass (temperature 0/None → greedy decoding), and it now uses
the tokenizer chat template for instruct checkpoints.

## Real-call validation (this container cannot reach chat.dartmouth.edu)

Network policy blocks `chat.dartmouth.edu`; OEIS / Wikipedia / Wikidata /
arXiv / Crossref / HF Hub are reachable. Per Constitution III the
validation used the *real* local transformers backend (an officially
supported fallback) through the identical router code path, plus the
real external claim sources:

- **Judge determinism (probe + permanent test)**: `judge_one()` ×3 on the
  verbatim PROJ-261 question via `Qwen/Qwen2.5-0.5B-Instruct` (local
  backend): 3/3 identical verdicts, no fail-opens, ~18 s/call; off-topic
  candidate correctly rejected. Cache round-trip: second call replays
  `cached=True` with no LLM call. `tests/real_call/test_relevance_judge_real.py`
  → 2 passed (77 s). Defaults to Dartmouth + qwen3.5-122b in nightly CI.
- **Claims layer on real sources**: `test_fill_oeis_real`,
  `test_fill_wikipedia_real`, `test_fill_wikidata_real`,
  `test_receipt_real`, `test_compute_real`, `test_verify_pi_e_real`,
  `test_local_backend` → **23 passed, 5 skipped** (all 5 skips =
  "No Dartmouth API key configured" fill steps; covered by
  `llmxive-real-call-nightly.yml`).
- **promptfoo gate smoke (local backend)**: harness runs end-to-end in
  27 s; the production-parser assertion correctly REJECTED the 0.5B
  model's fenced-frontmatter output — the exact contract violation the
  gate exists to catch. (First attempt timed out at the python-worker
  300 s limit purely due to CPU contention with a concurrently running
  25-min pytest suite.)

## Regression caught and fixed during this work (honest record)

The Phase 0 deletion of the legacy root `prompts/` directory broke 12
offline tests (`test_planning_recall_prompt.py`,
`test_canonical_sweep.py`, `test_claim_subject_reuse.py`):
`prompts/claim_extraction.md` was NOT orphaned after all —
`src/llmxive/claims/extract.py` loaded it via `_PROMPT_PATH`, and the
zero-reference sweep missed that one consumer. Worse, the missing-prompt
path in `extract_claims` silently returns `[]` instead of failing fast,
so extraction made no backend call at all. (An initial "these fail on
origin/main too" diagnosis was wrong — an artifact of the editable
install importing package code from this tree while running the main
worktree's tests.)

Fix: the prompt was restored byte-identically at the canonical location
`agents/prompts/claim_extraction.md` (verified with `diff` against
`git show c7b96b2~1:prompts/claim_extraction.md`) and `_PROMPT_PATH`
repointed; all 14 affected tests pass. Note for a follow-up: the
silent-`[]` behavior on a missing extraction prompt violates
Constitution V (fail fast) and is what let this regression hide.

## Deliberate scope decisions

- **DSPy optimization (#216)**: not started — requires a labeled eval
  set that doesn't exist. The promptfoo gate is the prerequisite
  measurement infrastructure.
- **Orchestration-harness pilot / repo split (#263)**: audit Phase 3,
  explicitly optional there; needs a maintainer scope decision before
  any code moves.
