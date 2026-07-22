# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019c** — The `validator.py` file is present but the `validate_session` function is truncated and does not contain a complete implementation, and the required schema file `contracts/session.schema.yaml` is missing entirely. Both the runtime validation logic and the schema it must load are absent, so the task is not genuinely fulfilled.
- **T019** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/metrics_summary.csv
- **T027a** — The repository lacks the required `figures/completion_time.png` file, and the provided `visualizer.py` is truncated and does not show a concrete function that generates a completion‑time box plot (only a generic private method). Consequently the task’s specified output and dedicated implementation are missing.
- **T027b** — The repository contains a partially‑implemented `visualizer.py` with a generic `_create_boxplot_with_ci` method, but no concrete function that creates the Error Count plot and saves it as `figures/error_count.png`. Moreover, the expected output file `figures/error_count.png` is absent. The task’s required artifact is therefore missing.
- **T027c** — The required output file `figures/sus_score.png` does not exist, and the provided `visualizer.py` only contains a generic `_create_boxplot_with_ci` method (truncated) with no concrete SUS‑specific function that saves to the required filename. Consequently the task’s deliverable is missing.
- **T029b** — declared artifact(s) missing/empty/invalid: github/workflows/reproducibility_check.yml
- **T029c** — declared artifact(s) missing/empty/invalid: github/workflows/reproducibility_check.yml
- **T030** — No notebook, seed‑pinning code, exact file‑path usage, or checksum verification for generated figures was provided. Without these artifacts there is no evidence that the notebook is fully deterministic as required.
