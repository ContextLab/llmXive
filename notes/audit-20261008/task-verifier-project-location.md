# Ground task verification in the observed project location

The single failed-only retry of PR #1532 passed reference-service checks but
failed `canonical-command-True`: the verifier rejected a repository-root command
when its evidence named only the project-relative `code/main.py`. It also correctly
objected that the fixture script was an 18-byte `print("analysis")` stub rather
than an implementation of the documented `--limit` argument. The failure is in
run 37939337333, job 113857377705.

The fixture now uses argparse with a required integer limit, bounds it to 1–1000,
and computes `sum(range(limit))`. Before semantic verification, subprocess checks
prove the commands execute from project, repository, or code directories and
produce 499500 for a limit of 1000. The missing-argument control proves omission
fails with argparse exit code 2. A single live pass after this fixture correction
passed five of six cases in 28.99 seconds, but the canonical command still failed:
the verifier could not establish the project's repository-relative prefix from
collector evidence. Retrying that unchanged input would not fix the evidence gap.

The collector now identifies its actual caller project under `projects/<id>` and
adds each observed file's repository-relative canonical location. These mappings
come from resolved filesystem paths, never generated artifact prose. Standalone
directories outside the production `projects/` convention receive no invented
repository identity. Missing or foreign-project paths remain missing; the original
task is passed unchanged and the verifier's scientific/semantic policy is unchanged.

The six original live cases remain, and a seventh negative control documents a
command under the wrong project prefix. Assertions still require the configured
primary model and the exact expected completion decision. Deterministic tests
cover real project/file identity, standalone directories and foreign-project paths;
the 34 related verifier/feedback/integration tests pass, as do Ruff and diff checks.

One post-correction live pass passed all seven cases in 120.98 seconds using the
configured primary model (the test asserts the observed model for every call).
The prior fixture-only failure was retained as before/after evidence; no unchanged
failed case was repeatedly rerun to obtain a favorable result.
