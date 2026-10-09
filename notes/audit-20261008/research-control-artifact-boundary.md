# Research implementation artifact trust boundary — 2026-10-09

## Reproduced defect

On baseline `49eb037df38`, a disposable project's task required computing the
exact sum of totients for integers 1 through 1000. Its code contained only
`VALUE = 1`, so the deterministic artifact check correctly deferred judgment.
The research implementation writer nevertheless accepted a model-authored
`.specify/memory/task_verify_cache.yaml` containing a publicly computable
evidence hash and `c: true`.

After that write, `verified_done_keys` returned the task as independently
accepted, and `run_verification_pass` reported one acceptance without calling
the independent verifier. The proof replaced that call with an assertion, used
only temporary files, and made no model call or production/canary change.

A second reproduction supplied `specs/invented/tasks.md` as an implementation
artifact. Existing slug canonicalization redirected it to the active task list;
the response replaced the reviewed definitions and dropped an outstanding task.
Both regression tests fail against the original writer.

## Direct artifact guard

Research implementation artifacts now cannot write components named `.specify`,
`.tasks`, `.git` or `.venv`, checked case-insensitively in both the original
proposal and resolved target. A symlink or feature-slug normalization cannot
hide a protected destination. The active specification, plan and task list,
including nonstandard feature locations, are also protected, as are standard
older feature definitions. Their dedicated author/reviewer stages remain the
place to revise those inputs.

The existing refusal path retains the task as open and supplies the exact reason
on the next attempt. Ordinary implementation code, data and documentation,
including feature research notes, quickstart, data model and contracts, remain
writable. Trusted platform writes to verification state and task markers are
unchanged; the guard applies to model-proposed artifacts.

## Validation and remaining boundary

27 new cases cover protected paths, existing-byte preservation, in-project
symlink aliases, project-prefixed paths, a protected component obscured by slug
normalization, active tasks replacement, nonstandard active feature locations,
forged acceptance caches and legitimate document outputs. After inheriting the
bounded refusal recovery from #1550, 85 related research writer, paper writer
and implementation-reviser tests pass in 2.34 seconds.
Ruff and `git diff --check` pass.

This is **not** an operating-system sandbox. Research Python/shell execution
still runs in the process/venv environment and may write files the artifact
writer refuses. Authentication of task-verifier cache entries is a separate
coordinated fix; this guard alone does not close executed-code forgery or
same-user access to host credentials. No full scientific acceptance or live
production closure is inferred from these tests.
