# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The repository contains a `code/main.py` file, but the shown excerpt stops before any CLI argument parsing or logic that writes a `stress_curves.parquet` file, and the required `data/derived/stress_curves.parquet` file is absent. Consequently the orchestration script does not demonstrably generate and save the stress curves as specified.
- **T030a** — The required `data/validation/human_annotations.csv` file is absent, and the provided script itself admits it can only produce a template with placeholder or simulated scores—not genuine human‑annotated intelligibility ratings. Both the missing output file and the reliance on simulated data mean the task’s core requirement is not satisfied.
- **T030b** — The repository lacks the required input files (`data/validation/human_annotations.csv` and `data/derived/stress_curves.parquet`), and the shown portion of `code/metrics.py` does not contain any implementation of the HVCM calculation described in the task. Consequently the primary regression target is not derived as specified.
- **T029** — declared artifact(s) missing/empty/invalid: data/validation/human_annotations.csv
- **T030** — declared artifact(s) missing/empty/invalid: data/derived/regression_results.json, data/derived/sensitivity_analysis.csv
