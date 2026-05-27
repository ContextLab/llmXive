# Contract: Carry-forward Manifest (FR-015 / SC-008)

`specs/014-phase4-plan-tasks-testing/carry-forward.yaml`. Schema mirrors `specs/011-…/carry-forward.yaml`, with an added `analyze_rounds` field on the Tasker entry.

```yaml
spec: 014-phase4-plan-tasks-testing
generated_at: <ISO-8601 UTC>
final_commit: <sha|HEAD>
projects:
  - project_id: <full PROJ id-slug>
    final_state: <analyzed | human_input_needed | held>
    status: <passed | failed | held>
    final_commit: <sha|HEAD>
    agents_run:
      - {name: planner, iterations: <int>, final_outcome: <outcome>}
      - {name: tasker,  iterations: <int>, final_outcome: <outcome>, analyze_rounds: <int>}
    justification: <one line; on failure/hold MUST cite the inspection-record path>
```

## Rules

- One entry per reference project (PROJ-261, PROJ-262).
- `status: passed` REQUIRES `final_state: analyzed` AND the recorded `final_state` matching the on-disk `state/projects/<id>.yaml` `current_stage` (SC-008).
- A failed/held project MUST record the stage it stopped at and a one-line reason citing the inspection path.
- Validates against a pytest schema check in `test_phase4_plan_tasks.py`.
