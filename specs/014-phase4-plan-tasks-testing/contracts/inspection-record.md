# Contract: Inspection Record (FR-003 / FR-004)

One JSON file per `(project, agent)`: `specs/014-…/inspections/<project_id>/<agent>.json`. Written by the existing `_inspection.capture` (opt-in via `LLMXIVE_INSPECTION_DIR`), extended with a `rounds` array.

## Required top-level keys

Same as spec 011 (existing records remain valid), plus `rounds`:

```
project_id, agent_name, agent_version, model, backend,
started_at, ended_at, duration_s, outcome,
reset_artifacts, prompts, raw_response, parsed_output,
file_diffs, error, rounds
```

- `agent_name` ∈ {`planner`, `tasker`}.
- `outcome` ∈ {`committed`, `abstained`, `failed`, `held`, `no-op`, `escalated`}.
- `prompts` = `{system: str, user: str}` verbatim.
- `file_diffs` = `{<relpath>: <unified diff str>}` for every file written.
- `reset_artifacts` = list of paths deleted by FR-018 before this invocation (`[]` if none).
- `rounds` = `[]` for the Planner; for the Tasker, one entry per analyze round:

```
{round_index:int, analyze_report:str, mode_b_patch:object|null,
 verdict:str, files_rewritten:list[str], diffs:object}
```

## Guarantees

- **Commit-safe** (FR-004): `_inspection._redact` removes API keys/tokens; only model id + truncated request id retained. A test asserts no secret-shaped strings remain.
- **Atomic** write (`_inspection._atomic_write`).
- **SC-009 reconstruction**: a reader can reconstruct what each agent was asked and returned — including every Tasker analyze round — from this file alone.
- **SC-005**: 100% of agent invocations AND Tasker rounds produce a record; a missing record fails the validation.
