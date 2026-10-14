# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/verify_plan_scope.py exit=1
- **T004** — Checked `code/requirements.txt`; it pins many scientific packages but the required `lammps` entry is only a commented note and not an actual pinned version, so the file does not contain pinned versions for all packages the spec lists. The missing active `lammps==...` line means the task requirement is not fully satisfied.
- **T010** — Requested task execution failed; rerun successfully: code/data/run_md_sim.py exit=1
