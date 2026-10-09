# Implementation context and CLI execution

The live canary reached implementation at 03:14 UTC after the task-analysis reuse
fix. Its T006 CLI was immediately marked failed because `execute: true` launched
`python code/src/totient_tv.py` without either required argument. Actual stderr:
`the following arguments are required: --max-n, --prime` (exit 2). The artifact
execution contract exposed no way to supply arguments.

The contract now accepts a list of literal argument strings; the sandbox passes
them directly to the Python subprocess without shell interpretation. Malformed
argument values fail before execution, missing required arguments still fail,
and execution logs retain the supplied argument list. The model prompt explains
how to use the active run instructions.

Inspection also found that the implementer saw tasks, sibling APIs and referenced
source, but not the active specification, plan or quickstart. These documents and
the original idea are now included verbatim. Recent execution logs for the current
task are included so retries see the actual stderr instead of only an exit-code
annotation. Other tasks' old failures are excluded.

Validation: 61 related tests pass. The new regression executes an actual generated
CLI through the implementer and project venv, writes/reads JSON output, verifies
literal shell-looking argument text, verifies credential stripping, and confirms
that omitting required flags still fails. File-backed prompt tests verify the
active constraints, invocation and exact prior failure reach the model. This does
not establish full scientific acceptance of the live canary.

A subsequent live attempt rejected a valid package initializer because the static missing-import check treated Python's implicit `__path__` as undefined. The guard now recognizes package globals for `__init__.py`; an actual subprocess import verifies the namespace-package pattern while an ordinary module still rejects undefined `__path__` and genuinely missing names.
