# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No `state/setup_dirs_verified.json` file was presented, nor any evidence that the required directory hierarchy (`code/`, `data/`, etc.) exists. Without the JSON listing absolute paths and timestamps, the verification condition cannot be satisfied. The implementer must create the directories and produce the specified JSON file that the script exits with status 0 only when all directories are present.
- **T004** — The log file exists, but the required schema contract files `contracts/ingest.schema.yaml` and `contracts/dataset.schema.yaml` are not present (no evidence of their existence or content). The task is not satisfied until those YAML files are created with the appropriate field definitions.
- **T016** — declared artifact(s) missing/empty/invalid: data/logs/pipeline.log
- **T022** — The submission contains only the task description and specification excerpt; there is no code, data, results, or report demonstrating a null baseline (mean prediction) comparison, the R² > 0.0 classification, or a permutation‑test p‑value calculation. Consequently, the required artifact proving the “learnable” classification logic is missing.
