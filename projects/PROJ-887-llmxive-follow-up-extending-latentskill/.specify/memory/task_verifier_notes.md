# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T014b** — The required output file `data/processed/skill_index.npz` is missing, and there is no evidence that `src/retrieval/vector_db.py` was run or that the index was created and verified. The implementer must execute the script to generate the index file and provide confirmation of its existence and integrity.
- **T022c** — The script `src/validation/generate_ground_truth.py` exists, but the required output artifacts `data/processed/composite_ground_truth.npz` and `data/processed/pairs.yaml` are not present on disk. Without these files the task’s core requirement—generating and saving the synthetic composite adapters and their metadata—is unmet. The next implementer must run the script (or ensure it creates) and verify that both output files are created and contain the expected data.
