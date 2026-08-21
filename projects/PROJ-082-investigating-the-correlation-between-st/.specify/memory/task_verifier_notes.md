# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009b** — The provided `code/data/real_data_validator.py` is truncated (ends with `logging.inf`) and lacks a runnable entry point that counts studies, raises a warning/error when N < 10, and writes the required `data/processed/real_data_status.json`. Moreover, the status JSON file is missing entirely. The task’s core functionality and output artifact are not present.
- **T014** — The `meta_analysis.py` file is truncated (e.g., incomplete `run_random_effects_model` definition, missing `import csv`, and no visible logic that actually reads the study count at runtime). Moreover, the required `data/processed/study_count.json` file does not exist, so the gate‑logic cannot be satisfied. The implementation therefore does not meet the task’s specifications.
