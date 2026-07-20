# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T007** — declared artifact(s) missing/empty/invalid: src/data/loaders.py
- **T009** — The implementer provided no configuration files, scripts, or documentation for environment management or checksum verification of raw downloads; no artifacts exist to demonstrate that these requirements were addressed. The task remains unfulfilled.
- **T012** — The required file `src/data/fetch_gbif.py` does not exist, so no code was provided to retrieve GBIF records, deduplicate them, or perform spatial thinning. The task’s core artifact is missing.
- **T013** — declared artifact(s) missing/empty/invalid: src/data/fetch_climate.py
- **T014** — declared artifact(s) missing/empty/invalid: src/modeling/train_rf.py
- **T015** — declared artifact(s) missing/empty/invalid: src/modeling/metrics.py
- **T016** — No code, tests, or documentation showing that error handling for “No occurrence records” and “Model training failure” (with retry using a reduced `max_depth`) was added. The required artifact (e.g., updated pipeline scripts, exception handling logic, and corresponding unit/integration tests) is missing, so the task is not satisfied.
- **T017** — The implementer provided no code, configuration, or log files that add provenance or thinning‑statistics logging, nor any evidence (e.g., screenshots, test outputs) showing such logging in action. Consequently the required artifact is missing.
- **T020** — declared artifact(s) missing/empty/invalid: src/data/fetch_traits.py
- **T023** — No code, script, configuration, or log files were provided that implement the required logic to detect missing trait data, flag or exclude those species, and record the exclusion reasons. Consequently, the task’s core requirement (FR‑006) is not demonstrated.
- **T024** — No code, configuration files, or documentation were presented showing that the known (T021a) and imputed (T021b) trait data have been incorporated into the Random Forest training pipeline, nor that the spec‑compliant path is set as the default. The required artifact (e.g., updated pipeline script, config file, or test output confirming the default behavior) is missing.
- **T028a** — declared artifact(s) missing/empty/invalid: src/analysis/stats.py
