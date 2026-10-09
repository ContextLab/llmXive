# Task verifier: missing local dependency context (2026-10-09)

The immutable-source canary (`1d2b4287245cf12cdb01ff9d367d9157229101ca`, project
`PROJ-9999-totient-canary`) exposed two different problems. No live scientific
files, checkboxes, stages, or counters were edited during this investigation.

## Platform defect

T007's persisted verifier feedback said `tests/test_tv.py` could not import
`analysis.analyze` because no analysis module was present in its evidence.
`code/analysis.py` did exist and supplied `analyze` with the expected return fields.
The collector only included paths literally declared by the task, so it omitted
that dependency and its `utils` dependency. Changes to those dependencies also
failed to invalidate the task's cached verdict.

The fix statically collects bounded project-local Python import candidates,
including imports inside functions, relative imports, package initializers and
transitive imports. It includes source bytes and SHA-256 hashes in the existing
evidence fingerprint. It never imports or executes project code, excludes paths
outside the project, exposes ambiguous candidate layouts, and explicitly warns
that a local candidate is not proof of runtime resolution or test success.
File, candidate and parse budgets report incomplete context rather than implying
that every dependency was inspected.

## The scientific task still failed

An untouched copy of the task's actual Python files was tested separately from
the canary. `tests/test_tv.py` had **10 passing tests and one failing test**.
The integration import succeeded. The failure was the test's assertion that the
third frequency for counts `[2, 3, 5, 0, 1]` equals `0.5`; it is actually `5/11`.
Enriching context must not turn this into an accepted task.

A real GLM-5.3 replay using the enriched packet plus the actual copied-snapshot
pytest log rejected T007 for this exact arithmetic error in 13.64 seconds. It no
longer claimed the existing analysis module was missing. Two real GLM-5.3 fixture
cases also passed in 18.53 seconds: an existing dependency with a passing test was
accepted, and an incorrect dependency with a failing test was rejected. Both
asserted the observed primary model, without accepting a fallback as equivalent.

Local proof files are in
`/private/tmp/llmxive-verifier-dependency-repro-20261009/`: the captured source
SHA-256 manifest, original task/spec text, enriched evidence, actual execution
record, and `real-verifier-replay.json`.

## Separate task-plan defects (not changed)

T008 requires verification of a CSV, but the ordered task list assigns CSV export
to later T009. Its generated `tests/test_stratum_csv.py` also imports
`export_stratum_csv` from `io`; a copied-snapshot run fails collection because
Python resolves standard-library `io`. A project file named `code/io.py` is not
proof that this import works. These remain research task/interface failures for
bounded autonomous recovery, not reasons to weaken acceptance or hand-edit the
scientific artifacts.

## Regression evidence

- Both new dependency-context and persisted-cache mutation regressions fail
  against the original `gather_evidence` function.
- 69 focused collector/verifier/feedback/paper-implementation checks pass.
- Boundaries cover symlink loops and relative escape, multiple local layouts, nested
  and transitive imports, package initializers, cycles, malformed Python,
  creation/mutation of a dependency, and explicit collection budgets.
- Two actual primary-model fixture calls and the captured-task replay pass as
  described above. These are verifier checks, not full-pipeline acceptance.
