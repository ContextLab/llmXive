# Repair diagnosis follow-up for issue #1242

Observed run: https://github.com/ContextLab/llmXive/actions/runs/37897943625

Attempt 3 selected project initialization for filesystem collisions recorded at
`in_progress`, proposed unconditionally unlinking the existing `code` file, and
generated a test assigning `config.repo_root` even though the initializer uses
the already-imported `_repo_root` binding. The candidate's regression failed;
the run reported one failure and five passes and never reached independent
review. This was not an accepted repair. A directory-name collision alone does
not prove initialization is the failing caller.

The repair runner now supplies dispatch facts extracted from the current graph
without importing it. These identify the default agent and its source where
statically available, but explicitly require investigation of hooks, alternate
dispatch and callees. They do not constrain a repair to that agent. Selected
source also yields explicit imported dependency bindings, so test generation
can patch the namespace actually used by the caller, restore it with pytest's
monkeypatch fixture, and check that operations stay within the test directory.

Raw evidence remains unchanged in evidence.json; derived dispatch and import
facts are separate artifacts. Retry feedback retains filenames for baseline,
candidate and preservation logs, and the Actions summary shows bounded tails.
The proposal instructions require recoverable existing bytes rather than
unconditional deletion.

Validation: 51 focused repair tests passed, including the existing fixed
preservation suite and independent-review routing tests. The new prompt-context
and labeled-retry regressions both failed against the baseline source and pass
with this change. Ruff and git diff --check passed. No preservation test or
acceptance gate was weakened. No research files or scientific canary artifacts
were changed. A new live repair run is still required to assess proposal quality
and must pass baseline/candidate tests, the separate fixed preservation suite,
and independent-model review before publication.
