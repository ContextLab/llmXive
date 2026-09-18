# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The required `contracts/dataset.schema.yaml` file is absent, and `code/ingestion.py` does not read or validate against such a schema (it uses hard‑coded column lists instead). Consequently the script cannot halt with “FATAL: Dataset Mismatch” based on the missing schema as the task demands.
- **T013** — No code, script, or log file implementing the subject‑validation logic is provided; the claim lacks any artifact showing how fMRI and MWQ data are joined, how unmatched pairs are excluded, or how counts are logged. The required implementation and its output are missing.
- **T014** — No code, script, log file, or filtered dataset was provided to demonstrate that per‑subject mean FD > 0.5 mm subjects are excluded, that exclusion counts and IDs are logged, and that a filtered dataset is output. The required artifacts are missing.
- **T015** — No code, script, log file, or test output showing a zero‑variance check, warning, or logged exclusion count is provided; without such artifacts we cannot confirm the requirement was implemented. The implementer must supply the updated ingestion/processing code (or a diff) and example logs demonstrating the exclusion count.
- **T016** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_data.csv
