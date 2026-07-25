# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009** — declared artifact(s) missing/empty/invalid: src/utils/timeout_utils.py
- **T010** — No evidence of a `data/prompts/` directory or the four required placeholder `.txt` files is provided; without these artifacts the task’s requirement cannot be confirmed as satisfied. The implementer must add the directory and create the four specified files.
- **T013** — declared artifact(s) missing/empty/invalid: src/ingestion/download_datasets.py
- **T013b** — No code, script, or test output was provided that shows validation logic filtering out entries with missing code or non‑string types, nor any logs confirming excluded entries. The required artifact (implementation of the exclusion logic) is missing.
- **T013c** — declared artifact(s) missing/empty/invalid: data/processed/corpus.csv
- **T014** — declared artifact(s) missing/empty/invalid: data/processed/corpus.csv
- **T015** — The required artifact `src/utils/checksum_artifacts.py` is missing entirely, so no hashing functionality is present to integrate with the preprocessing pipeline. The task cannot be considered done until this file is created with the appropriate code.
- **T016** — No code, log files, or documentation were provided showing that excluded entries are now logged or that peak memory usage is recorded and compared against the SC‑004 constraint. Without these artifacts, we cannot confirm the required logging functionality was added.
- **T021** — declared artifact(s) missing/empty/invalid: src/execution/run_inference.py
- **T022** — No script, configuration, or log files were provided that demonstrate seeds being pinned or the required logging of prompt text, model version, and seed for each request. Without concrete artifacts showing this deterministic‑execution functionality, the task’s requirement is not satisfied.
- **T023** — No code, script, or directory structure was provided showing that translation outputs are being saved under `data/evaluation/raw_translations/` with sub‑folders for each prompt condition. Without such artifacts, we cannot confirm the required storage implementation exists.
- **T024** — No code, script, or log modifications were provided to demonstrate that the system now records a “failed translation” entry when the LLM returns non‑code text. Without an artifact showing the added logging logic (e.g., updated inference or post‑processing module and example log output), the requirement cannot be confirmed.
- **T025b** — declared artifact(s) missing/empty/invalid: src/evaluation/generate_translations_log.py, data/evaluation/raw_translations_log.csv
- **T025** — The required artifact `tests/contract/test_test_translation.py` does not exist in the repository, so the contract test for test translation is missing. The task cannot be considered completed until this file is created with appropriate test content.
- **T027a** — The submission contains only the task description and project spec excerpt; there is no artifact that selects a deterministic transpiler nor any documentation describing its usage, configuration, or determinism guarantees. A concrete selection (e.g., `transcrypt` version) and accompanying documentation are required to satisfy T027a.
- **T027** — declared artifact(s) missing/empty/invalid: src/evaluation/translate_tests.py
