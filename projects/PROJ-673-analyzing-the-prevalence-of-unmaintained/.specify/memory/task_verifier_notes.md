# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8`, or related setup scripts) are present, and the only artifacts shown pertain to the NPM dependency analysis feature, not to configuring ruff/flake8/black. Consequently, the required linting/formatting setup is missing.
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/cache.py
- **T008b** — No code, data, or report was provided that demonstrates a local file caching mechanism being exercised in a real pipeline simulation, nor any evidence that such a verification was performed. The required artifact (e.g., a script, logs, or test results showing the caching behavior) is missing.
- **T017a** — No code, configuration file, or documentation was provided showing a `TOP_PACKAGES` default value being set. The required artifact (e.g., a source file or settings entry defining the default count) is missing, so the task is not satisfied.
- **T017b** — No code, dataset, or script was provided that demonstrates the calculation of `age_in_days` with the required behavior (null `release_date` → `age_in_days` null, while still having a non‑null `vulnerability_count`). The artifact needed to verify the logic is missing.
- **T018** — The provided `src/cli/collect_data.py` does not contain any code that writes `data/processed/dependencies_raw.csv` or `data/processed/metrics.json` (no references to those filenames appear in the shown portion), and the expected output files are absent from the repository. The export logic required by the task is missing.
- **T019** — The required output artifacts `data/processed/dependencies_raw.csv` and `data/processed/metrics.json` are absent; there is no evidence that the `collect_data.py` script was executed or that it produced the expected files, nor that it fails loudly if creation fails. The task’s core deliverable is therefore missing.
- **T020** — declared artifact(s) missing/empty/invalid: data/processed/dependencies_raw.csv
- **T023** — declared artifact(s) missing/empty/invalid: src/analysis/power.py
- **T024** — declared artifact(s) missing/empty/invalid: src/analysis/power.py, data/processed/power_analysis.json, data/processed/dependencies_raw.csv
- **T027** — The required output file `data/processed/results_correlation.json` does not exist, and the provided `src/analysis/correlation.py` only defines helper functions without any code that runs the analysis and writes the JSON result. Consequently the task of executing the script to generate the correlation results has not been fulfilled.
- **T030** — No code, script, or report artifact was provided that implements the required logic to flag statistical significance (p < 0.05) in the US‑2 output report. Without a concrete file showing the flagging behavior, the task requirement is not satisfied. The next implementer must add and commit the updated analysis/report generation code (or a sample output) that includes the significance flag.
- **T034** — declared artifact(s) missing/empty/invalid: src/analysis/stratified_stats.py
- **T035** — declared artifact(s) missing/empty/invalid: src/analysis/stratified_stats.py
- **T036** — The required script `src/analysis/stratified_stats.py` does not exist, and the output file `data/processed/results_correlation.json` is also missing, so the variance calculation cannot have been executed nor the results stored.
- **T037** — declared artifact(s) missing/empty/invalid: src/analysis/sensitivity.py
- **T038** — declared artifact(s) missing/empty/invalid: src/analysis/sensitivity.py, data/processed/sensitivity_analysis.json
- **T040** — The `generate_report.py` script is present, but the required output file `docs/report.md` does not exist, so the aggregation step has not been demonstrated. The missing report file must be generated and present for the task to be considered complete.
- **T041** — No `docs/` directory or `quickstart.md` file was provided; the claim of documentation updates cannot be verified because the required artifacts are missing. The task requires actual documentation files to be present and contain instructions for running the pipeline.
