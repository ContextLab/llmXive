# Execution retry context (2026-10-09)

The fresh canary's final verification script repeatedly opened a manifest under its current project ID, while its generator wrote the task-specified old ID. The log clearly named both paths, but a task naming only `docs/quickstart.md` did not include the failed script's actual contents. Likewise, earlier script failures remained unresolved while later edits omitted their execution requests.

Build referenced-file context from the selected task plus its recent execution logs and run-book failure feedback, using the existing bounded project-path resolver and dependency context. Document the runtime's existing ability to execute an unchanged script by omitting `contents`, and require rerunning each command named in a failed-execution annotation. This avoids forcing wholesale rewrites merely to retry a command; acceptance still requires actual success and independent review.

Validation: 37 focused tests pass. A real shell script first fails on a missing prerequisite, then succeeds through an execution-only request after that prerequisite exists; its contents and mtime remain unchanged. A production prompt test proves the failed source reaches a task that only names an output directory.

Related to #1139. Live repair convergence is not established by these tests.
