# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`src/bias_pipeline`, `src/cli`, `data/raw`, `data/processed`, `data/validation`, `tests/unit`, `tests/integration`, `state`) is presented; without visible artifacts the claim cannot be confirmed. The implementer must provide a listing or screenshots showing the created project structure.
- **T003** — No configuration files (e.g., pyproject.toml, .ruff.toml, .pre-commit-config.yaml) or any other evidence of ruff and black being set up are provided; without such artifacts the claim that linting/formatting tools are configured cannot be verified.
- **T006** — No evidence was presented showing that a `data/` directory with the subfolders `raw`, `processed`, and `validation` actually exists; the claim is unsubstantiated. The required directory structure must be created and verified (e.g., via a file listing) to satisfy the task.
- **T007** — The `lexicon.py` file exists but its `load_lexicon` function only attempts to read a local CSV and raises an error if the file is absent; there is no implemented fallback to fetch from a verified HuggingFace URL. Moreover, the required `data/raw/lexicon.csv` file is missing from the repository. Consequently, the module cannot fulfill the task of loading the curated demographic lexicon as specified.
- **T043** — No `error_handler.py` file or any code showing it being imported and used in the implementations of US1, US2, or US3 is present. The required artifact (error handling integration) is missing, so the task is not satisfied.
- **T051** — No `spec.md` file or its contents are provided, so we cannot confirm that it was updated to include the “Fairness Degradation Slopes” methodology or that any contradiction with `tasks.md` was removed. The required artifact is missing.
- **T041** — No validation dataset file, download script, or reference to a specific HuggingFace dataset ID is present in the provided artifacts. The claim lacks any concrete CSV, dataset link, or code that acquires or validates manually labeled comments, which is required by task T041. The implementer must supply the actual dataset (e.g., a CSV with 200 manually labeled comments) or a reproducible script that fetches a verified external dataset.
- **T012** — The required integration test file `tests/integration/test_extractor.py` is missing entirely, so no test code exists to verify handling of empty or binary‑only repositories. The task is therefore not satisfied.
- **T013** — declared artifact(s) missing/empty/invalid: src/bias_pipeline/extractor.py
- **T014** — declared artifact(s) missing/empty/invalid: src/bias_pipeline/extractor.py
- **T015** — declared artifact(s) missing/empty/invalid: src/bias_pipeline/extractor.py
- **T016** — declared artifact(s) missing/empty/invalid: src/bias_pipeline/extractor.py
- **T017** — declared artifact(s) missing/empty/invalid: src/bias_pipeline/extractor.py
