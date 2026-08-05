# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T018** — declared artifact(s) missing/empty/invalid: data/raw/github-code-sample.csv
- **T017** — The `code/pii_scanner.py` implementation is present, but the required input file `data/raw/github-code-sample.csv` does not exist, so the scanner cannot actually scan the specified dataset. Without this file the task’s core requirement (scanning that CSV for PII) cannot be fulfilled.
- **T053** — declared artifact(s) missing/empty/invalid: data/processed/semantic_distance.csv
- **T053b** — declared artifact(s) missing/empty/invalid: data/processed/semantic_distance.csv
- **T021** — The repository contains a `main.py` with functions to compute and save the metrics and a join‑validation routine, but the `run_pipeline` implementation is truncated and the required output files `data/processed/clone_metrics.csv` and `data/processed/perplexity_scores.csv` are not present. Without a complete pipeline that actually creates those CSVs, the task’s requirement is not satisfied.
- **T021b#1** — No `main.py` file or diff showing the fix is present, and there is no evidence (e.g., generated CSV files, logs, or tests) that the script now reliably creates both required CSV outputs. The required artifact is missing, so the task is not satisfied.
- **T023** — No code, test, log file, or documentation was provided that demonstrates a memory‑monitoring mechanism during inference, nor any evidence (e.g., test results, screenshots, metrics) showing that the model stays within the required memory limit. The required artifact is missing.
- **T062** — No code, test files, or log output demonstrating that a segment‑count threshold is checked and recorded are present. The claim consists only of a textual description without any concrete artifact (e.g., implementation, unit test, or logged evidence), so the requirement is not satisfied.
