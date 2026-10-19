# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T003** — The `src/models/trainer.py` fails to import the real `sdv` package because the local `rdt` module still shadows the dependency, causing an ImportError and preventing `generate_and_save` from creating the required CSV and JSON files (the `outputs/synthetic/` directory is empty). Consequently the unit tests in `tests/unit/test_trainer.py` fail, so the task’s functional and output requirements are not met. Fix the import‑shadowing issue (and ensure early‑stopping logic) so that the trainer runs and the synthetic files are written.
- **T004** — Requested task execution failed; rerun successfully: src/cli/run_fidelity.py exit=1
