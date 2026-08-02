# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — The repository lacks the required `data/processed/games.parquet` file, and the provided `src/main.py` is truncated and does not show a call to the validation function, saving of the parquet file, or any exit‑code handling. Consequently the script does not demonstrably meet the specification.
- **T027** — The repository lacks the required `data/results/model_metrics.json` and the `model_output.schema.yaml` files, and the provided `src/models/fit.py` does not contain any code that fits Beta or Ridge models and writes their coefficients, p‑values, R², or AIC to a JSON file. Consequently the task’s core requirement is not satisfied.
