# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory listings or other evidence were provided to show that the required folders (`data/raw`, `data/processed`, `data/results`, `code/`, `tests/`, `state/`) actually exist on disk. Without concrete proof of the created project structure, the task cannot be confirmed as completed.
- **T002a** — No evidence of a Python virtual environment (e.g., a `venv/` directory with activation scripts, `pyvenv.cfg`, or installed packages) is present. The required artifact is missing, so the task of creating the venv has not been demonstrated.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, `black` settings) or documentation of their setup are present. The claim provides only unrelated project specifications, so the required linting/formatting tooling is not demonstrated.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T020** — No JSON file `data/results/metrics_{subject_id}.json` (or any similar artifact) was presented; therefore the required metric extraction and saving step cannot be verified. The implementer must provide the actual JSON output files containing the `subject_id` and `transition_count` fields for at least one subject.
- **T020a** — The repository lacks a defined `aggregate_metrics_to_tsv()` function in `code/metrics.py` (the file is truncated and does not show such an implementation), and the required output file `data/processed/metrics_aggregated.tsv` is absent. Both the implementation and the generated TSV are missing, so the task is not satisfied.
- **T022** — declared artifact(s) missing/empty/invalid: data/metrics_log.txt
- **T025b** — The provided `code/analysis.py` does not contain any iteration over `Subject` objects nor a check using `Subject.has_valid_data()`, and there is no code that writes the count of excluded subjects to `data/analysis_log.txt`. Additionally, the required log file does not exist. These essential parts of the task are missing.
- **T028** — declared artifact(s) missing/empty/invalid: data/analysis_results.tsv
- **T030** — I looked for PNG files in the `data/results/` directory named `plot_{metric}_{behavior}.png` (e.g., `plot_reconfigurability_speed.png`) and found no such files or any scatter‑plot images at all. The required output artifacts are missing, so the task is not satisfied.
- **T034** — declared artifact(s) missing/empty/invalid: data/results/permutation_results.tsv
- **T035** — No PDF or PNG file was found in `data/results/` showing a null‑distribution histogram with the observed statistic highlighted. The required visual report is missing, so the task is not satisfied.
- **T036** — declared artifact(s) missing/empty/invalid: data/analysis_log.txt
- **T036a** — No README.md content was supplied, so we cannot verify that it exists, is non‑empty, or contains the required CLI usage examples and installation instructions for the `code/` and `data/` directories. The implementer must provide the updated README file showing those sections.
