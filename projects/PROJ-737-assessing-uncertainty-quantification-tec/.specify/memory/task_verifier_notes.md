# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of the required directories (`data/raw/`, `data/processed/`, `code/models/`, `code/metrics/`, `code/stats/`, `results/`, `tests/unit/`, `tests/integration/`, `code/utils/`) being present on disk is provided. The implementer must create and show these directories for the task to be considered complete.
- **T002** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black config) or any lint/format check reports are present. Without these artifacts, the requirement to configure ruff and black is not satisfied.
- **T002c** — No `spec.md` file or excerpt is provided, so we cannot confirm that SC‑005 has been updated to list “Band Gap, Thermal Conductivity, Formation Energy.” The required artifact is missing.
- **T024a** — No `results/per_sample_errors.csv` (or any schema definition file) was presented. The required columns and saved location are missing, so the contract is not established.
- **T015** — No evidence of a modified `pipeline.py` containing the required try/except blocks, error logging, skipping logic, or partial‑result saving is provided; the artifact is missing, so the task cannot be confirmed as completed.
- **T021** — declared artifact(s) missing/empty/invalid: results/metrics_raw.csv
- **T024#1** — No artifact such as a script invoking `run_paired_wilcoxon`, nor the required `statistical_report.csv` (or any output showing paired Wilcoxon test results) is present. The implementer has not provided evidence that the per‑sample errors were processed or that the correct statistical test was executed, violating the task’s core requirement.
- **T027** — declared artifact(s) missing/empty/invalid: results/statistical_report.csv
- **T028** — declared artifact(s) missing/empty/invalid: results/sensitivity_report.csv
