# Task scope and replanning context

The canary still had 30 implementation tasks despite the bounded-study system
prompt. The tasker's user context supplied a generic application template with
roughly 30 sample tasks, API endpoints, authentication, blocking infrastructure,
and separate polish phases. Its skeleton also encouraged root `src/` even when
working artifacts existed in `code/src/`.

Replace that template with an eight-task research example: execute a small valid
case early, complete the specified domain and comparisons, check independent
correctness and runtime, generate actual tables/figures, and hand reproducible
results to the paper stage. Scientific requirements remain authoritative; the
8-15 target permits justified exceptions and never deletes existing verified work.
The tasker reads the current platform template before stale project-local copies.

A second context defect was confirmed by inspection: the tasker separately read
peer reviews, but did not call the common helper that includes the precise
kickback diagnosis and independent-verifier notes. It now uses that helper, so
replanning can repair the actual failure while preserving working artifacts.

Validation: 14 tasker context/engine integration tests pass. The new file-backed
context regression includes the real templates, a stale project template,
verified work, all original parameter constraints, and concrete failed-import
feedback. Actual generated task-count improvement awaits a new live planning pass.

A further live check found the T007 schema already existed under the active
feature, but `contracts/summary.schema.yaml` resolved only at the project root.
Contract shorthand now resolves to the active feature when no root artifact
exists. Explicit repo-rooted paths and existing root contracts retain precedence.
The file-backed regression checks both valid evidence and these boundaries.

Full CI exposed the repository's strict synchronization of 903 project-local
copies of the vendored Spec Kit template, plus its template-classification test.
The research template therefore lives at `agents/templates/research-tasks.md`,
read directly as one platform resource. The vendored template is restored byte
for byte; its synchronization and classification checks remain intact. This avoids
rewriting hundreds of irrelevant project scaffolds to deploy research policy.
