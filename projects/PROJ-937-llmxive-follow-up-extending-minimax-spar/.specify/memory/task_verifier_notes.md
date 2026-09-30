# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`code/`, `data/raw`, `data/processed`, `results`, `tests/unit`, `tests/integration`) is provided; the artifacts listed pertain only to feature specifications and testing scenarios, not to the filesystem structure. The implementer must create and show these directories (e.g., a directory listing or file tree) to satisfy the task.
- **T003** — The provided evidence contains only the feature specification for sparse‑attention heuristics and no configuration files, scripts, or documentation for ruff or black. There is no `.ruff.toml`, `pyproject.toml` with black settings, or any other artifact showing that linting/formatting tools have been set up, so the task requirement is not met.
- **T024** — declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- **T025** — No code, configuration, or log output was provided that adds the required logging of exclusion counts for corrupted or missing “needle” strings in the RULER dataset. The artifact is missing entirely, so the task’s requirement is not satisfied.
- **T032a** — No code, script, data file, or documented output implementing the false‑positive‑rate calculation for the sensitivity analysis (selection without target vs Dense Attention) was provided. The required artifact is missing, so the task’s core requirement is not satisfied.
- **T032b** — declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- **T031** — declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- **T033** — The implementer did not provide a `quickstart.md` file or any documentation showing CPU‑only execution instructions; only a feature specification and test scenarios are present, which do not satisfy the documentation update requirement. The required markdown artifact is missing.
- **T035** — No test run logs, result files, or any indication that a full `pytest` suite was executed on a CPU‑only runner and that all tests passed are present. The implementer provided no artifacts to verify the required pytest execution.
- **T036** — The required artifact `results/benchmark_report.json` does not exist, so there is no content to check for the specified keys. Without the file, the verification cannot be performed. The implementer must create the JSON file with the listed metrics.
