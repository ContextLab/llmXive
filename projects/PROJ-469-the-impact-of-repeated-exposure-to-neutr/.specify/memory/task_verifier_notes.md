# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No evidence of a logging configuration or error‑handling code was provided in the `code/` directory, nor is there a `logs/` folder or any script that sets up console logging. The required artifact (logging infrastructure) is missing, so the task is not satisfied.
- **T038** — declared artifact(s) missing/empty/invalid: code/data_fetcher.py
- **T014** — The repository contains `code/preprocessing.py`, but the file is truncated and does not show any code that writes the imputed DataFrame to `data/processed/imputed_data.csv`. Moreover, the missingness‑>50% case logs an error and raises a `ValueError` rather than logging a warning as required. The expected output CSV is absent, so the task is not fully satisfied.
