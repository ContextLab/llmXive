# Contract: Phase Report (SC-010 / SC-011)

`specs/014-phase4-plan-tasks-testing/phase-report.md`. Human-readable Markdown produced by `scripts/validate_phase4.py` after both canonicals run.

## Required sections

1. **Summary** — one line per canonical: `<project_id>: <start stage> → <final stage> (planner: <outcome>, tasker: <outcome>, <n> analyze rounds)`.
2. **FR → evidence** — a table mapping each spec FR-NNN to the artifact/test/inspection path that demonstrates it (or "n/a — not exercised this run" with reason).
3. **Quality-gate findings** — every silently-broken behavior caught, NAMING the offending `inspections/<id>/<agent>.json` path (SC-010). Empty list ⇒ explicit "no findings".
4. **Mode-B coverage** (SC-011) — states, per project, whether Mode-B was exercised on real content (≥1 real analyze round, with the inspection path) and confirms the synthetic regression tests cover it regardless.
5. **Carry-forward** — restates the `carry-forward.yaml` verdict per project.

## Rules

- Every claim that a criterion is met cites concrete evidence (a file path, a test name, or an inspection path) — no bare assertions (Principle II).
- If any FR is "not exercised", the report MUST say why and whether that blocks carry-forward.
