# Offline integration contract audit — 2026-10-09

Base: `89aa1c922eb` (main). The hygiene audit exposed six failures that also occurred on its unchanged base. Re-running the original six tests against this fresh main checkout reproduces **6 failures in 0.18 seconds**.

## What was stale

Five canonical-sweep / subject-reuse tests supplied `specs/001/spec.md` without a stage label and expected post-planning claim resolution. The production service now deliberately recognizes research planning artifacts by their paths, so a missing or non-planning caller label cannot bypass planning deferral. The observed `[deferred]` output and absence of newly registered/resolved claims are correct for these spec artifacts. This contract was already tested separately in `test_planning_artifact_role.py`.

The corrected fixtures use `docs/research.md`, where canonical correction and subject reuse actually apply. Existing assertions remain: wrong counts are replaced, verified facts persist, unrelated numbers remain, the rephrased claim carries the exact prior evidence and source hash, and absent twins are not reused. These five cases pass without changing production behavior.

The sixth test expected `RuntimeError` from a one-task stub. Production correctly emits the more precise `TaskFormatError` (a `ValueError`) before writing, with the existing minimum-five requirement. The test now expects that type and the exact minimum-count diagnostic and still asserts that no `tasks.md` was written. No minimum-count or scientific gate changes.

## Added coverage and validation

- Four new boundary cases explicitly retain planning deferral for a planning artifact with no stage, a planning artifact edited by an implementer, and a research-shaped path in an explicitly planning stage. A seeded subject twin does not cause planning to register or preverify a new claim.
- The service docstring now describes artifact-based routing instead of incorrectly promising that `stage_label=None` always selects full resolution. Executable production code is unchanged.
- The six corrected tests plus new boundary cases and surrounding canonical/plan-task tests pass: **78 passed in 4.23 seconds**. Fixtures are deterministic extraction responses and real temporary filesystem state; these are offline contract tests, not evidence of live model quality.
- Full offline suite: **3,351 passed, 20 skipped, 4 deselected** in 431.44 seconds (`tests/unit tests/contract tests/integration -m "not slow"`). Four pre-existing unregistered `slow` marker warnings remain. Ruff and `git diff --check` pass. An additional focused artifact-role/task-format run passed 17 tests.
