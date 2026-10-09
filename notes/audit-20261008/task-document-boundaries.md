# Task document parsing and write boundaries

At 2026-10-09 02:51 UTC, the canary's implementation stage rejected its generated
task list before a model call. The report named the fenced format example
`- [ ] T### ...` as malformed, alongside eight genuinely duplicated task IDs.
The tasker had already spent two full generation/analysis passes on that document.

All execution, independent verification, checkbox completion and task-marking
consumers now mask fenced Markdown examples while preserving source offsets and
example bytes. Matching backtick/tilde delimiters are required; an unterminated
fence is a format error rather than a way to hide unfinished work.

Research and paper task generation validate canonical identities before replacing
existing tasks. The shared convergence/legacy writeback guard uses the same
validation and counts only actual tasks. Duplicate IDs and malformed pending
checkboxes are refused before expensive downstream implementation or analysis.
Existing valid artifacts survive a refused writeback; no scientific requirements
or completed statuses are automatically rewritten by this change.

Validation: 134 focused tasker, implementer and independent-verifier tests pass.
Regressions exercise file-backed generation refusal, engine guards, exact task
marking, completion, nested-length fences, and verification with real-looking IDs
inside examples. This is deterministic platform validation; full canary acceptance
remains pending.

Research and paper taskers also unwrap an outer Markdown response wrapper before
checking identities, while retaining inner examples. Example-only paper responses
are rejected before overwriting prior work. Sixty-six boundary, planning and
paper-stage tests pass after this follow-up.
