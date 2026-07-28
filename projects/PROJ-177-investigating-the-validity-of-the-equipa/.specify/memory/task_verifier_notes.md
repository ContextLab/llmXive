# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required project directories (`code/`, `data/`, `artifacts/`, `tests/`) is provided; the claim lacks any artifact listing or file tree confirming their existence. The task therefore remains unverified.
- **T016** — No code, script, or notebook was provided that adds a `pot_incomplete` boolean column to the output DataFrame or emits the required warning log when the z‑axis data is missing. Consequently the required artifact is absent.
- **T017** — No `energy_samples.csv` file was presented in the evidence, nor any listing of its location under `data/derived/`. Consequently the required output file with the specified columns is missing, so the task is not satisfied.
- **T021** — The `code/stats.py` file only defines a binning function that expects a DataFrame argument and never reads `data/derived/energy_samples.csv`. Moreover, the required CSV file is absent from the repository. Both the input data and the required reading logic are missing, so the task is not fulfilled.
