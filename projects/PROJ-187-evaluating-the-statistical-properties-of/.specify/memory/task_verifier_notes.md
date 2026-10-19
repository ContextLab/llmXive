# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T003** — The verification test `pytest tests/unit/test_trainer.py` fails (exit 1, both tests FAILED with an `ImportError: cannot import name 'HyperTransformer' from 'rdt'`), and no `outputs/synthetic/*.csv` artifacts exist, so there is no evidence any model actually trained or produced synthetic data. Additionally, the trainer never implements the mandatory FR-013 early stopping (delta=0.001, patience=3) — the parameters are accepted but ignored — and the seed is never passed to the SDV models, so FR-017 reproducibility is not honored; the failure path also writes an empty header-only CSV rather than r
- **T004** — Requested task execution failed; rerun successfully: src/cli/run_fidelity.py exit=1
