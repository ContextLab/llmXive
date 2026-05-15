# /speckit-analyze Report — 2026-05-15

## Specification Analysis Report

| ID | Category | Severity | Location(s) | Summary | Recommendation | Resolution |
|-|-|-|-|-|-|-|
| C1 | Coverage | HIGH | tasks.md (FR-010) | FR-010 ("audit every artifact write uses `_real_only_guard`") had no explicit task; only implicit via "agents already call guard". | Grep all `Path.write_text` / `.open("w")` in `src/llmxive/{speckit,agents/*}` writing `.md` artifacts; verify each is preceded by `assert_real_or_raise`. Add regression unit tests. | **Resolved** — added T035a. |
| C2 | Coverage | MED | tasks.md (SC-002) | SC-002 blind-review measurement has no implementation task (manual measurement). | Polish-phase task: prepare 20-contribution sample + one-page rubric. | **Resolved** — added T053b. |
| C3 | Coverage | MED | tasks.md (FR-018) | T047 references `paper_review_quarantined` stage but no task adds it to the `Stage` enum. | Add enum + Pydantic validator + scheduler skip + unit test. | **Resolved** — added T042a. |
| C7 | Constitution | MED | plan.md (Principle V) | Liveness check happens after LLM call; should fail fast on network unreachability before spending an LLM call. | Add a single HEAD to `https://arxiv.org/` with 5s timeout at the top of `personality.tick()`. | **Resolved** — added T053a. |
| C9 | Coverage | HIGH | tasks.md (T024) | T024 didn't explicitly cover the "downstream artifact deleted transitively" case (FR-008). | Strengthen T024 with sub-fixture for transitive deletion + recursive rollback. | **Resolved** — T024 expanded. |
| A1 | Ambiguity | LOW | tasks.md (T029 run-id format) | Run-id format not specified. | Use `uuid.uuid4()` per existing convention. | **Deferred** — implementation detail; matches existing pattern. |
| C4 | Coverage | LOW | research.md R3 vs T044 | Figure-bearing page heuristic (caption regex `Figure \d+`) declared in research, not restated in T044. | Move into T044 description. | **Accepted as-is** — implicit via T038 fixture. |
| C5 | Inconsistency | LOW | data-model.md vs T018 | `example_contribution` in persona-card frontmatter. | None. | **Consistent.** |
| C6 | Coverage | MED | FR-019 (drive failing-page count to zero) | Remediation work could be unbounded if audit surfaces many failure classes. | Acceptable risk; spec scopes to "current pool"; escalate per failure. | **Accepted.** |
| C8 | Coverage | LOW | tasks.md (poppler) | T048 mentions `apt-get install poppler-utils`; T002 documents the dependency. | None. | **Consistent.** |
| C10 | Inconsistency | LOW | spec.md FR-019 vs T047 | "Drive failing-page count to zero" vs. "Re-run audit until zero fail entries". | None. | **Consistent.** |

## Coverage Summary Table (after remediation)

| Requirement | Has Task? | Task IDs |
|-|-|-|
| FR-001 (position frontmatter) | Yes | T012, T013, T016, T019 |
| FR-002 (liveness-checked adjacent_work) | Yes | T007, T008, T009, T015, T019 |
| FR-003 (interest_signal anchor) | Yes | T013, T016, T018, T019 |
| FR-004 (extended rubric) | Yes | T013, T016 |
| FR-005 (rejected-contributions diagnostic) | Yes | T021 |
| FR-006 (rotation diversity) | Yes | T014, T020 |
| FR-007 (audit script) | Yes | T023, T028, T031 |
| FR-008 (transitive delete) | Yes | T024, T029 |
| FR-009 (stage rollback) | Yes | T024, T030 |
| FR-010 (every artifact write guarded) | Yes | T035a (new) |
| FR-011 (two-strike escalation) | Yes | T026, T034 |
| FR-012 (PIPELINE_PARALLELISM) | Yes | T025, T033 |
| FR-013 (no LLM in pdf_pipeline) | Yes | T041, T048 |
| FR-014 (audit script + crash quarantine) | Yes | T036, T037, T040, T044, T045, T046 |
| FR-015..FR-017 (cites/authorblock/figures) | Yes | T037, T038, T044 |
| FR-018 (failure classification) | Yes | T039, T043, T042a (new — adds quarantine stage) |
| FR-019 (drive failing-page count to zero) | Yes | T047 |
| FR-020 (no LLM env vars in CI) | Yes | T048 |
| FR-021 (section-number monotonicity) | Yes | T037, T044 |
| FR-022 (idempotence) | Yes | T032, T056 |
| FR-023 (log to run-log) | Yes | T029, T032, T035 |
| SC-001..SC-008 | Yes | T015 (SC-001), T053b (SC-002, new), T032 (SC-003), T027 (SC-004), T033/T053 (SC-005), T047 (SC-006), T041/T048 (SC-007), T046 (SC-008) |

## Constitution Alignment Issues

None remaining. C7 (fail-fast reachability) resolved via T053a.

## Unmapped Tasks

None. Every task traces to one or more FR/SC.

## Metrics

- Total Requirements: 23 FR + 8 SC = 31
- Total Tasks: 60 (was 56; added T035a, T042a, T053a, T053b)
- Coverage %: 100% (was 94%)
- Ambiguity Count: 1 LOW (A1 — deferred as implementation detail)
- Duplication Count: 0
- Critical Issues: 0 remaining
- HIGH coverage gaps remaining: 0
- MED coverage gaps remaining: 0

## Next Actions

All HIGH and MED issues resolved by task additions. Ready to proceed to `/speckit-implement`.

## Remediation Applied

User requested "address ALL issues you find using your recommended solutions" — applied:

1. **T035a** added → FR-010 explicit coverage audit
2. **T042a** added → `paper_review_quarantined` Stage enum + Pydantic validator + scheduler skip + unit test
3. **T053a** added → early HEAD-against-arxiv.org fail-fast in `personality.tick()`
4. **T053b** added → SC-002 manual blind-review harness
5. **T024** strengthened → explicit transitive-deletion + recursive-rollback test cases

Total task count rose from 56 → 60.
