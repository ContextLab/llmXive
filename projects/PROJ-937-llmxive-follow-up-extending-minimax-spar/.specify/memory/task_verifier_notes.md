# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`code/`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`) is provided; the only artifact shown is a feature specification, not a project folder structure. The implementer must create and show these directories (with at least placeholder files) to satisfy the task.
- **T003** — The provided evidence only describes user stories and testing for sparse‑attention heuristics; there are no ruff or black configuration files, scripts, or documentation present. Consequently, the required linting/formatting setup is missing.
- **T018** — No code changes or files were presented showing a fallback implementation in `code/heuristics/`; the evidence lacks any artifact that selects the first k blocks when scores are near‑zero. Consequently the required logic is missing.
- **T024** — declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- **T025** — No code, configuration, or log output was presented that adds logging for exclusion counts when RULER samples are corrupted or lack the “needle” string. The required artifact (e.g., modified inference script, logging statements, or example log file) is missing, so the task’s requirement is not satisfied.
- **T031** — declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- **T032a** — No code, script, data file, or documented output implementing the false‑positive‑rate calculation for the sensitivity analysis (selection without target vs Dense Attention) was provided. The required artifact is missing, so the task’s core requirement is not satisfied.
- **T032b** — declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- **T033** — The implementer did not provide a `quickstart.md` file or any documentation showing CPU‑only execution instructions; only a feature specification and test scenarios are present, which do not satisfy the documentation update requirement. The required markdown artifact is missing.
- **T035** — No test run logs, result files, or any indication that a full `pytest` suite was executed on a CPU‑only runner and that all tests passed are present. The implementer provided no artifacts to verify the required pytest execution.
- **T036** — The required artifact `results/benchmark_report.json` does not exist, so there is no content to check for the specified keys. Without the file, the verification cannot be performed. The implementer must create the JSON file with the listed metrics.
