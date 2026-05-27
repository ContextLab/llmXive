# Contract: Regression & Schema Tests (FR-016, FR-010, SC-006)

File: `tests/integration/test_phase4_plan_tasks.py`. Every test exercises the REAL guard/validator code path (Principle III); only the LLM body (or, for FR-006, the HTTP server) is controlled, because the test's subject is the guard, not the model.

## Six FR-016 regression tests

| # | Test | Real code under test | Method |
|-|-|-|-|
| a | FILE-marker split | `plan_cmd._split_multi_file` | feed a 5-file marker block; assert all 5 keys present; feed a malformed/duplicate marker; assert fail-closed (no partial commit) |
| b | invented/unreachable URL rejection | `_research_guard.assert_urls_reachable` | local `http.server` returns 200 (pass), 404 + 500 + timeout (each raises `UnreachableReference`); assert Planner `write_artifacts` unlinks + raises |
| c | prose-stub tasks.md rejection | `tasks_cmd` Mode-A task-ID validator (`< 5` → raise) | feed a prose `tasks.md` (`<5` `T###`); assert RuntimeError, no advance |
| d | Mode-B diff-leak | `_diff_guard.refuse_if_diff` / `looks_like_diff` in Mode-B path | feed a Mode-B patch that is a unified diff; assert rejected |
| e | Mode-B header preservation | Mode-B per-patch header check (`<1 header` → skip) | feed a spec.md/plan.md rewrite that drops all `#` headers; assert skipped/rejected |
| f | analyze-loop cap → human_input_needed | `tasks_cmd` `range(TASKER_MAX_REVISION_ROUNDS)` + escalate branch | drive a never-clean analyze; assert `human_input_needed.yaml` written, stage holds at `analyze_in_progress`, run-log `escalated` |

## Plus

| Test | Asserts |
|-|-|
| FR-005 completeness | `_research_guard.assert_artifact_set_complete` raises `IncompleteArtifactSet` on a 4-file set, an empty artifact, and a no-marker (`{plan.md:…}`) response; passes on the full 5-artifact set |
| FR-007 consistency | `_research_guard.assert_data_model_contracts_consistent` raises `InconsistentDataModel` on entity↔schema mismatch; passes when aligned |
| FR-008 template rejection | `_real_only_guard.guard_emit` raises `TemplateRefused` on a template-equal `plan.md`; the Planner unlinks + fails |
| FR-012 constraint non-deletion | the `validate_phase4` check flags a Mode-B `spec.md` rewrite that drops an `FR-NNN`/`SC-NNN` line; passes a non-reducing rewrite |
| FR-010 ordering | the `validate_phase4` ordering check flags a consumer-before-producer `tasks.md` and passes a correctly-ordered one |
| inspection schema (SC-006) | a sample record has every required key incl. `rounds`; a Tasker sample reconstructs each round; `_redact` leaves no secret-shaped strings |
| carry-forward schema | a sample `carry-forward.yaml` parses and matches the contract |

## Determinism

- FR-006 uses a real local HTTP server (real sockets) — no `urllib` mock.
- No test makes a real Dartmouth call (those happen in `scripts/validate_phase4.py`, the real-call e2e).
- All tests pass in the standard `pytest` run with no network beyond localhost.
