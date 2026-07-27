# Spec 025 slice 1A/1B implementation — running notes

**Branch:** `025-self-improvement-lane`. **Nothing pushed** (rebase onto `origin/main`
at PR time only; local `main` lags and cron commits constantly).

## Where things stand

Plans (both maintainer-reviewed through **round 7**, all findings resolved):
- `docs/superpowers/plans/2026-07-24-025-slice1a-durable-substrate.md` — **14 tasks**
- `docs/superpowers/plans/2026-07-25-025-slice1b-proposal-convergence.md` — **10 tasks**
- Spec is at **rev 16** (`specs/025-self-improvement-lane/spec.md`).

### Implementation progress

| Task | State | Commit |
|-|-|-|
| 1A T1 — extract `git_event_log.py`, rewire `ledger_transport` | DONE | `7a179b49c8` (+ plan fix `a20e005857`) |
| 1A T2 — lane `Event` + validation + `TYPE_VALIDATORS` | DONE | `a270b6927e` |
| T1/T2 round-8 review: two fail-open gaps closed | DONE | `abdb8d1536` (+ plan `6e805708de`) |
| 1A T3 — `lane_log.py` on the shared core | DONE | (this commit) |
| 1A T4 — `LaneCoordinator` projection | next | — |
| 1A T5–T14, 1B T1–T10 | not started | — |

## Money-path acceptance bar (T1)

The seven files in the plan's Global Constraints MUST pass with **no edits**:
baseline **135 passed** (42 + 93) before the extraction, **135 passed** after.
Re-run this whenever `git_event_log.py` or `ledger_transport.py` changes:

```
python -m pytest tests/integration/test_credit_ledger_transport.py \
  tests/integration/test_credit_reservations.py \
  tests/integration/test_model_selection_execute.py \
  tests/unit/test_ledger_config_from_env.py \
  tests/unit/test_model_selection_attempt_hooks.py \
  tests/unit/test_model_selection_inventory.py tests/unit/test_paid_credits.py -q
```

## Decisions made DURING implementation (plans updated to match)

1. **Ledger exceptions are SUBCLASSES + boundary translation, not aliases.**
   Rounds 2–6 specified `LedgerError = GitLogError` etc. so `except Ledger*` would
   still catch what the core raises. Correct as far as it goes — but aliases make
   `type(exc).__name__` report `GitLogContention`, and `execute` formats that name
   into its candidate notes, so `test_reserve_ledger_error_skips_not_aborts`
   (money path, uneditable) failed. Now: `Ledger*` subclass `GitLog*` (multiple
   inheritance, so `except GitLog*` also works) **plus** `_as_ledger_error()`
   wrapping every entry point that calls the core, so no base instance escapes.
   Plan corrected in `a20e005857`.

2. **`read_log` deliberately does NOT sync/verify.** Only `append_to_log` and an
   explicit `sync_and_verify`/`fetch_ledger` do — matching the credit ledger's
   existing split. A test that expects the pinned-anchor check on a bare read is
   wrong (I wrote one; fixed).

3. **Barrier seams need a PER-THREAD one-shot**, not a shared `Event` flag: with a
   shared flag one thread sets it and waits while the other skips the wait, and the
   first blocks until `BrokenBarrierError`. Use `{thread_ident} -> already_waited`
   under a lock so each worker waits exactly once, on its first attempt.

4. **Absence and failure must never collapse** (round-8). `[]`/`None` from the log
   means "no claim, no reservation, no spend" to every projection, so an operational
   failure reported that way is fail-OPEN. Discriminators, established empirically:
   `rev-parse --verify --quiet` exits **128** on operational failure but **1 for BOTH**
   a missing ref and an unreadable object → disambiguate with `show-ref` (exit 1 = ref
   truly absent). `ls-tree` exits 0 with EMPTY output for an absent path, 128 on
   failure — so it is both the checked listing in `read_log` and the existence test in
   `_read_event_blob` (`cat-file` cannot tell the cases apart; both exit 128).

5. **Presence is not a schema** (round-8). The envelope validates TYPES: non-empty
   strings, non-bool non-negative ints (`True == 1` and hashes as 1 — a boolean `seq`
   would order the projection as position 1), and tz-aware timestamps (FR-011 is an
   instant, not a date).

6. **`_finalize` stamps ALL FOUR revision anchors** (T3), not just the target scope's two.
   The plan's version left the other scope as the caller passed it, so a coordinator event
   built by the plan's own `_ev` helper (which pre-fills `expected_problem_revision`)
   failed validation with "lane-stream event must NOT set the problem revision scope". The
   store is the sole authority for these fields, so it writes the target scope and clears
   the other. Verified load-bearing by reverting it (1 test fails).

7. **`config=LaneLogConfig()` as a signature default is ruff B008.** Resolved the way the
   sibling `ledger_transport._log_ref` already does it: `config: LaneLogConfig | None =
   None`, resolved inside `_log_ref`. Plan signatures updated to match.

## Known-failing, NOT caused by this work

`tests/unit/test_dataset_sources.py::test_openml_*` (2) fail in this sandbox: they are
real-network calls to openml.org. Verified independent by stashing all lane work and
re-running — same two failures. Do not "fix" by weakening; they need network.

## Standing constraints (do not drift)

- Commit each task with `PRE_COMMIT_ALLOW_NO_CONFIG=1`, trailer
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`; verify HEAD moved.
- **Never weaken a test** — fix the code so existing tests pass.
- Behavior-preserving when the new hooks/params are absent; the full non-slow suite
  must stay green.
- No model-id literals outside the canonical `model_selection` layer
  (`enforcement.py` enforces it statically).
- Real tests, no mocks. Protocol test doubles implementing real logic are fine;
  `unittest.mock` is not the primary path.

## Next step

1A Task 4: `LaneCoordinator` projection — the first CONSUMER of `lane_log.read`, so it
inherits the fail-closed reads for free. Task 4's full text is in the 1A plan.
