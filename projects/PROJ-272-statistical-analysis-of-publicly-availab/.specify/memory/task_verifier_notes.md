# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012b** — The repository contains `code/ingestion.py`, but the provided excerpt shows no function that counts raw records and writes the result to `data/results/raw_record_count.json`. Moreover, the required `data/results/raw_record_count.json` file is absent from the project. The task’s core output is therefore missing.
- **T012e** — The repository lacks a `data/results/metadata.json` file, and the shown portion of `code/ingestion.py` does not contain any logic that logs participant counts per group, issues a warning for groups with fewer than 10 participants, or writes a `"low_power"` flag to metadata. Consequently, the task’s requirements are not met.
- **T012f** — declared artifact(s) missing/empty/invalid: data/raw/checksums.json
- **T014** — The repository lacks the required `data/interim/exclusions.log` file, and the shown portion of `code/ingestion.py` does not contain any implementation of the record‑filtering logic or logging of excluded records with reason codes. Consequently, the task’s core requirement is not satisfied.
- **T016** — declared artifact(s) missing/empty/invalid: data/interim/cleaned_adress.csv
- **T012h** — declared artifact(s) missing/empty/invalid: data/results/metadata.json
- **T011** — The repository contains the contract test `tests/contract/test_schemas.py`, but the required artifacts `data/interim/cleaned_adress.csv` and `data/results/metadata.json` are absent, so the test cannot actually validate the dataset schema or the `valid_label_proportion` key. The missing files must be created with appropriate content for the task to be complete.
- **T024** — The required `data/processed/embeddings.npy` file does not exist, and the accompanying `embeddings.derivation.log` is only a placeholder that has not been populated with real execution details. Consequently, the semantic feature extraction has not been fully implemented or executed as specified.
- **T024c** — declared artifact(s) missing/empty/invalid: data/processed/embeddings.npy, data/processed/checksums.json
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/features.csv
- **T027** — The repository lacks the required output file `data/results/statistical_metrics.json`, and the provided excerpt of `code/stats.py` shows no implementation of Bonferroni correction or any code that writes raw and adjusted p‑values to that JSON file. Both the correction logic and the persistence step are missing, so the task is not fulfilled.
- **T028** — The required output file `data/results/statistical_metrics.json` is missing, so no Cohen's d calculations have been persisted as specified. The task’s core deliverable is absent.
