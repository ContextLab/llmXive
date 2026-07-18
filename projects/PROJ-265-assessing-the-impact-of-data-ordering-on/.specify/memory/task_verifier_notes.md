# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `tests/`, `data/raw/`, `data/processed/`, `results/`) being present or populated is provided; the artifact list is empty, so the initialization task is not demonstrated as completed.
- **T032** — No code, configuration, or documentation for error handling and logging logic for real‑world data was supplied. The claim lacks any artifact (e.g., Python modules, log configuration files, test cases) demonstrating that such functionality was added, so the requirement is not met.
- **T037** — The required file `tests/test_reproducibility.py` does not exist, so the function `verify_reproducibility()` that runs `runner.py` twice and compares the hash of `results/coverage_metrics.csv` is missing. The presence of `results/coverage_metrics.csv` alone does not satisfy the task.
- **T039** — The required test file `tests/test_reproducibility.py` does not exist in the repository, so the reproducibility verification cannot be run. The missing artifact must be added (and the test executed) to satisfy the task.
