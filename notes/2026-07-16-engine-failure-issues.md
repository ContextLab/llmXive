# Engine-failure issues + #314 — root cause & fix (2026-07-16)

Scope: all open `engine-failure` issues (#505, #515, #516, #517, #518) and the
escalation-digest issue #314. Goal: fix root causes, post evidence comments,
tests green.

## Findings

### #505 — `PermanentBackendError: Client Closed Request`
- HTTP **499** (upstream proxy closed the connection before the Dartmouth vLLM
  pod first-byte). Textbook transient, but `"client closed request"` was not in
  `dartmouth._TRANSIENT_ERROR_MARKERS`, so `_do_one_attempt` fell through to the
  catch-all `raise PermanentBackendError`. A permanent error → `_stage_panel`
  files an engine-failure issue (FR-016). A transient → `BackendUnavailable` →
  no issue, project retries next tick.

### #515–518 — `PermanentBackendError: 'API key invalid!'`
- Not our string — comes from Dartmouth's gateway. Key is **valid** (live catalog
  probe returns HTTP 200 / 43 models today). All four issues clustered in a
  ~2h window on **2026-07-06 (00:56Z→02:58Z)** then stopped — a transient
  auth-service flap, NOT a persistently-bad credential (which would fail every
  cron cycle continuously).
- Same misclassification: an unmatched auth string → `PermanentBackendError` →
  spurious engine-failure issue.

### #314 — escalation digest
- Every row was **PROJ-552** (2026-06-11..18), long resolved: post-mortem
  `notes/2026-06-11-proj-552-postmortem.md` + router `saw_transient`/`saw_outage`
  → `BackendUnavailable` fixes; project has since advanced to the **execution**
  stage (`state/execution_status/PROJ-552-…json`, total_attempts=16, 2026-07-13).
- Bug: escalation records were write-once/forever and `build_digest_markdown`
  rendered ALL of them → resolved rows never left the digest. A maintainer had
  worked around it by stuffing `"resolved: …"` into `digest_id` (a hack the body
  ignored).

## Fixes

### `src/llmxive/backends/dartmouth.py`
- Added `"client closed request"`, `"499"` to `_TRANSIENT_ERROR_MARKERS`.
- Added `_AUTH_ERROR_MARKERS` + `_is_auth_error_text`.
- Added `_gateway_rejects_key()` — a cached catalog-endpoint preflight (same key +
  host as chat); True only on a definitive 401/403; False on 200 or any
  indeterminate outcome ("cannot confirm the key is bad"); probes up to 3×.
- Added `_raise_for_backend_error(text, exc)` — THE single classification
  chokepoint: model-down → transient → auth-flap-when-key-valid → permanent.
  `_do_one_attempt` now delegates to it.
- Extracted `_catalog_get(key, timeout)` — single lazy `requests` import + auth
  header (used by `_fetch_cloud_models` and `_gateway_rejects_key`).
- Net: a transient flap (valid key) → `TransientBackendError` → no spurious
  issue; a genuinely bad key (catalog 401/403) → stays `PermanentBackendError`
  (fail-fast, loud). `_is_transient_error_text` stays a pure, over-match-free
  function so `test_permanent_errors_stay_permanent` is unaffected.

### `src/llmxive/state/escalations.py`
- `EscalationRecord.resolution` field + `_is_resolved()` (recognizes the legacy
  `digest_id:"resolved:…"` hack).
- `list_records(include_resolved=False)` default-excludes resolved.
- `resolve_records(project_id, note=…, stage=…, loop=…)` — clean resolution.
- `refresh_digest()` + `_find_digest_issue()` — re-render the live digest from
  unresolved records without waiting for a new escalation.
- `update_digest` body now resolved-free. `GhRunner` type alias annotates all
  `gh` params (fixed 2 pre-existing mypy no-untyped-def errors too).
- Marked the 5 stale PROJ-552 records resolved (audit trail preserved on disk).

## Tests (all real, TDD RED→GREEN)
- `tests/unit/test_dartmouth_retry.py`: +5 (client-closed-499, auth-error-matcher,
  auth-flap-transient, genuine-bad-key-permanent, classifier-precedence).
- `tests/unit/test_escalation_paths.py`: +5 (resolved excluded from listing/digest,
  resolution note persists, stage filter, refresh_digest repatches, update_digest
  omits resolved).
- Full offline suite: 6700 passed / 17 skipped. ruff + mypy clean on changed files.

## Direct evidence (fixed tree)
```
_gateway_rejects_key() [live]            -> False (key accepted)
#505 Client Closed Request               -> TransientBackendError
#515-518 API key invalid! (valid key)    -> TransientBackendError
genuine bad key (catalog 401)            -> PermanentBackendError
list_records() before/after resolve      -> 4 -> 0 (digest rows); 5 preserved w/ include_resolved
```

## Remaining GitHub ops (post-merge / live)
- Evidence comments posted on #505/#515/#516/#517/#518/#314.
- #314 body refreshes to zero rows via `refresh_digest` / next `update_digest`.
