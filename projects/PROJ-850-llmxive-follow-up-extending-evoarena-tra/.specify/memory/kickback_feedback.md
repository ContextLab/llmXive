# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states the 'EvoMem-Conflict' agent falls back to 'latest state only' if no conflicts are detected. This introduces a confound: the agent's performance on tasks with *no* conflicts will be based on a minimal context (latest state), while 'EvoMem-All' uses a full context. If the task requires historical context (even without explicit contradictions) to succeed, 'EvoMem-Conflict' will fail not because of the filtering logic, but because of the *absence* of context. This makes it impossible to distinguish between 'filtering noise' and 'discarding signal'. The methodology should ensure that 'EvoMem-Conflict' always retrieves a minimum context window (e.g., latest state + 2 most recent non-conflict patches) to ensure the agent has sufficient information, isolating the effect of *filtering* rather than *reducing context size*.
