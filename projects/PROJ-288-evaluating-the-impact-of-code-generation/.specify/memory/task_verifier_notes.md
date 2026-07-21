# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listing or other evidence was provided showing that the required folders (`code/data`, `code/analysis`, `data/raw`, `data/processed`, `data/baseline_corpus`, `tests/unit`, `tests/integration`, `docs/reports`) actually exist; without such proof the task requirement is not satisfied.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or corresponding GitHub Action/workflow files) were presented. Without these artifacts, the requirement to configure Ruff and Black cannot be verified as satisfied. The next implementer should add the appropriate configuration files and, if applicable, CI integration scripts.
- **T008** — declared artifact(s) missing/empty/invalid: data/run_logs.txt
- **T009** — No configuration files, scripts, or documentation for managing GitHub API tokens are present, and the provided project excerpt does not include any artifact related to environment configuration management. Consequently, the required setup for token handling is missing and the claim is not substantiated.
- **T011** — The required artifact `tests/unit/test_classify.py` does not exist in the repository, so no unit test for the classification heuristic logic is present. The task cannot be considered completed until this file is added with appropriate test code.
- **T012** — The required file `tests/integration/test_fetch_prs.py` does not exist in the repository, so the integration test for the API fetch with a mock response is missing. The task cannot be considered completed until this test file is added with appropriate test code.
- **T013** — The required output file `data/raw/prs_raw.json` does not exist, and the provided `repo_list.txt` format does not match the script’s expectations (the script expects “repo,star_count” lines, but the file only contains repo names). Consequently the script cannot fetch PRs as specified, nor can it produce the required raw JSON output.
- **T016** — declared artifact(s) missing/empty/invalid: data/manual_labels.csv, data/validation_log.csv
- **T017** — declared artifact(s) missing/empty/invalid: data/validation_log.csv
- **T023** — declared artifact(s) missing/empty/invalid: data/processed/pr_data_filtered.csv, data/analysis_results.json
- **T024** — declared artifact(s) missing/empty/invalid: data/analysis_results.json
- **T025** — declared artifact(s) missing/empty/invalid: data/analysis_results.json
- **T026** — declared artifact(s) missing/empty/invalid: data/analysis_results.json
- **T027** — declared artifact(s) missing/empty/invalid: data/analysis_results.json
- **T020** — declared artifact(s) missing/empty/invalid: tests/unit/test_models.py
