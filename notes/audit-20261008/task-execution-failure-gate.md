# Requested execution failures must block task acceptance

The isolated canary on 2026-10-09 at 05:27–05:30 UTC produced real nonzero
execution results for T008d, T009, T011b, T012 and T012b. The implementer
nevertheless marked each `[X]` with `FAILED-IN-EXECUTION`. Task verification
could delegate these known failures to a semantic model, and could reuse a
matching positive cached judgment. The existence of source code does not
establish that its requested execution succeeded.

The implementer now marks such attempts pending review. The verifier rejects
an execution-failure annotation deterministically, before semantic review or
cached acceptance, and uses the existing bounded rejection/replanning loop.
A retry clears a failure annotation only when every failed script named in it
actually executes successfully. Merely rewriting code, running another file,
or rechecking a box does not clear the failure. Unrelated task annotations
and sibling task IDs are preserved. Successful retries still require normal
independent semantic review.

Validation: actual shell subprocesses fail with exits 7/8, are rejected without
calling a model, then a real successful retry becomes eligible for independent
review. A historical checked task with an exactly matching positive cache is
also rejected. Those three behavioral regressions fail on the prior platform.
The correction does not rewrite any scientific canary artifacts or make any
claim of full-pipeline acceptance.
