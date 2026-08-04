# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T008** — No code, configuration file, or documentation was presented showing that environment variables for API keys (if needed) and random seeds have been set up or handled. Without any artifact to inspect, we cannot confirm the requirement has been met. The implementer must provide the actual implementation (e.g., a `.env` template, a settings module, or script snippets) that demonstrates the environment variable handling and seed configuration.
- **T012** — declared artifact(s) missing/empty/invalid: data/processed/metadata.csv
- **T014** — No code, configuration, or log output was provided to demonstrate that download progress logging and API response handling have been added. The required artifact (e.g., updated script/module with logging statements and/or sample log files) is missing, so the task is not satisfied.
- **T017** — The required artifact `tests/integration/test_retrieval.py` does not exist in the repository, so the integration test for retrieval on a sample spectrum is missing. Without this file, the task’s deliverable is not provided.
- **T018c** — No artifact defining the output schema (e.g., a JSON/YAML/CSV specification listing fields for log10 water mixing ratio, its standard deviation, and an upper‑limit flag) was provided. The claim lacks any concrete file or code that maps these values, so the requirement is not satisfied.
- **T019** — No code, script, or documentation was presented that implements detection of low‑S/N spectra using SNR/Resolution metadata, nor any logic that produces censored upper‑limit values. The required artifact is missing, so the task is not satisfied.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/retrieval_results.csv
- **T021** — No code, configuration, or log files were provided that demonstrate the added error‑handling logic (logging failures, attempting upper‑limit derivation, and continuing execution). Without concrete artifacts, we cannot verify that the requirement has been implemented.
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/analysis_results.json
