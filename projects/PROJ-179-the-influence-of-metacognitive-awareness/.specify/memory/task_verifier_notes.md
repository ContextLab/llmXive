# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — The required file `data/validate_data_availability.py` does not exist, so no code is present to perform the dataset existence and column checks. The task cannot be considered fulfilled until this script is created and implements the specified validation.
- **T005** — The required artifact `data/download.py` does not exist on disk, so no implementation of dataset fetching or checksum validation is present. The task’s core requirement is therefore unmet.
- **T006** — The required file `data/validate_data.py` does not exist in the repository, so the validation functionality cannot be present. The task’s core artifact is missing, making the implementation incomplete.
- **T012** — The required file `data/preprocess.py` does not exist in the repository, so no code was provided to extract trial‑wise source labels and responses from the VALID dataset. Without this artifact, the task’s core requirement is unmet.
- **T016** — The required output file `data/results/primary_analysis.json` does not exist, so the implementation has not produced the mandated JSON report containing the correlation magnitude, direction, p‑value, and confidence interval. The missing artifact must be created for the task to be considered complete.
- **T022** — The required artifact `data/results/regression_analysis.json` does not exist, so the implementation that should add regression coefficients, standard errors, t‑statistics, p‑values, and diagnostic flags cannot be verified. The missing file must be created and populated with the specified regression results.
