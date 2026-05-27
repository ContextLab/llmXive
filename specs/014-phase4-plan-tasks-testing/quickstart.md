# Quickstart: Phase 4 Validation & Hardening

## Prerequisites

- Dartmouth Chat key resolvable via `llmxive.credentials.load_dartmouth_key()` (do NOT read `os.environ` directly). Key lives in `~/.config/llmxive/credentials.toml` if not in env.
- Working tree on branch `014-phase4-plan-tasks-testing`.
- PROJ-261 and PROJ-262 at `current_stage: clarified` (verify: `grep current_stage state/projects/PROJ-26[12]-*.yaml`).

## Run the regression + schema tests (no backend, deterministic)

```bash
python -m pytest tests/integration/test_phase4_plan_tasks.py -v
```

All FR-016 (a–f) + FR-007/FR-010/schema tests must pass. They exercise the real guards (`_research_guard`, `_diff_guard`, `_real_only_guard`, `tasks_cmd` validators) with a local HTTP fixture for URL checks.

## Run the end-to-end validation on the real canonicals

```bash
# one canonical at a time; the driver does preflight + FR-018 reset + run + verify
python scripts/validate_phase4.py --project PROJ-261-evaluating-the-impact-of-code-duplicatio
python scripts/validate_phase4.py --project PROJ-262-predicting-molecular-dipole-moments-with
```

Under the hood the driver runs `python -m llmxive run --project <id> --max-tasks 2` with `LLMXIVE_INSPECTION_DIR=specs/014-…/inspections/<id>` set, so the Planner and Tasker write inspection records automatically.

## Verify outputs

```bash
# stage reached analyzed
grep current_stage state/projects/PROJ-261-*.yaml      # → analyzed

# five plan artifacts + tasks.md present, spec.md preserved
ls projects/PROJ-261-*/specs/001-*/                    # plan.md research.md data-model.md quickstart.md contracts/ tasks.md spec.md

# tasks.md has >=10 numbered tasks
grep -c '^- \[ \] T' projects/PROJ-261-*/specs/001-*/tasks.md   # >= 10

# inspection records exist (planner + tasker, tasker has rounds[])
ls specs/014-phase4-plan-tasks-testing/inspections/PROJ-261-*/  # planner.json tasker.json

# tasker round count
cat projects/PROJ-261-*/.specify/memory/tasker_rounds.yaml
```

## Carry-forward + phase report

After both canonicals pass, the driver writes:

- `specs/014-…/carry-forward.yaml` — both projects at `analyzed`, ready for Phase 5 (#49).
- `specs/014-…/phase-report.md` — FR→evidence table, quality-gate findings, Mode-B coverage statement.

## Expected end state

Both canonicals at `analyzed`; 4 inspection records; `carry-forward.yaml` lists both as `passed`; all regression tests green.
