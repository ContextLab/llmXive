# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002b** — The required `requirements.txt` file is missing, so no dependencies could be installed or verified in a virtual environment. Without the file, the implementer could not fulfill the installation and verification steps.
- **T006a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T009** — No `.env` file, configuration‑loading code, or documentation of relative‑path handling is present in the provided artifacts. The implementer has not supplied any evidence that environment configuration management was set up, so the requirement is unmet.
- **T018** — The `preprocessing.py` file does not contain any logic for detecting ACE outliers >3 SD or adding a flag column (the code is truncated and lacks such functionality), and the required output file `data/processed/cleaned_dataset.csv` is absent. Both the implementation and the resulting flagged dataset are missing.
- **T019** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset.csv
- **T029** — No output report artifacts were supplied, so there is no evidence that the findings are explicitly framed as “associational only.” The implementer must provide the actual report files (e.g., markdown, PDF, or HTML) and demonstrate that every statement about the relationship between early life stress and hippocampal subfield volumes uses associative language (e.g., “is associated with”) and avoids causal phrasing.
- **T030** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json, data/processed/model_results_summary.csv
- **T022** — The required artifact `tests/unit/test_results.py` does not exist, so no unit test for the Bonferroni correction logic is present. The task cannot be considered completed until this file is added with appropriate test code.
- **T037** — The required output file `data/processed/sensitivity_report.csv` does not exist, and the provided `code/analysis/robustness.py` (truncated) contains no logic for counting significant findings per threshold or writing a summary table with a variation metric. Consequently the task’s core requirement is unmet.
