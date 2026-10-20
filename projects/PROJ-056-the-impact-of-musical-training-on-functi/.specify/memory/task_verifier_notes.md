# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `code/run_quickstart_test.py` – it only checks for file existence and never validates the JSON/CSV files against their `*_schema.yaml` contracts, violating the requirement. It also expects `data/processed/connectivity_matrices.npy` which the synthetic pipeline in `code/main.py` does not create, so the test would fail even on file existence. These missing behaviors must be added to satisfy the task.
- **T002** — Requested task execution failed; rerun successfully: code/data/run_synthetic_generator.py exit=1
