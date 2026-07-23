# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or any setup scripts) are present, nor any documentation showing that Ruff and Black have been installed and integrated into the project. The claim lacks any concrete artifact demonstrating the required setup.
- **T004a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — No `.gitignore` file or snippet containing rules for `data/raw/`, `data/derived/`, and `data/artifacts/` was provided; without the actual file content we cannot confirm the required ignore patterns exist. The implementer must add a `.gitignore` entry (e.g., `data/raw/`, `data/derived/`, `data/artifacts/`) and supply the file as evidence.
- **T011c** — declared artifact(s) missing/empty/invalid: data/derived/failure_cases.json
- **T015a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T015b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T016** — No code, configuration, or log files were provided showing that logging for annotation counts and rule‑generation metrics was added. Without concrete artifacts (e.g., modified scripts, logging output, or documentation of the new logging behavior), the requirement cannot be verified as satisfied.
- **T022** — declared artifact(s) missing/empty/invalid: data/derived/baseline_results.json, data/derived/results.csv
- **T023** — No code, configuration, or output files were provided that demonstrate the addition of stratification logic or the recording of metrics separately for each failure type. The required artifact (e.g., updated metric‑logging module, test results showing separate “syntactic”, “semantic”, etc. metrics) is missing.
- **T024a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T024b** — declared artifact(s) missing/empty/invalid: data/derived/results.csv, schema.yaml
- **T026a** — declared artifact(s) missing/empty/invalid: data/derived/regression_results.json
- **T026b** — declared artifact(s) missing/empty/invalid: data/derived/regression_results.json
- **T035a** — No artifact (e.g., terminal output, log file, or CI report) showing that `ruff --check` was executed on the `code/` directory and returned exit code 0 is present. Without such evidence, we cannot confirm the linting pass. The implementer must provide a concrete proof of the successful ruff run.
- **T035b** — No evidence such as a command log, terminal output, or a recorded exit code is provided to show that `black --check` was executed on the `code/` directory and returned exit code 0. The required artifact confirming the formatting pass is missing.
