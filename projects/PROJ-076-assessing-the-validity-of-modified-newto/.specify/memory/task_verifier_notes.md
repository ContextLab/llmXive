# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directory hierarchy (`code/`, `data/`, `results/`, `tests/`, `state/`) is provided; the implementer’s claim lacks any artifact showing these folders exist or contain content. The task’s core requirement—creating the project structure—is therefore not satisfied.
- **T003** — The review found no linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or related setup scripts in the repository. Without these concrete artifacts, the requirement to configure ruff/flake8 and Black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- **T004** — The test file exists but the required schema file `contracts/dataset.schema.yaml` is missing, so the validators cannot be verified against the actual schema. Additionally, the `sample_galaxy_data` fixture creates columns of mismatched lengths, which would raise an error when the DataFrame is built, meaning the test cannot even run the validation logic. The implementation therefore does not satisfy the task’s requirement.
- **T025** — declared artifact(s) missing/empty/invalid: results/fit_summary.csv
- **T026** — The required output file `results/sensitivity_data.csv` does not exist, so the sensitivity analysis result is not produced. Additionally, the provided `code/sensitivity.py` is truncated and may not fully implement the described functionality. The missing CSV must be generated for the task to be considered complete.
- **T035** — declared artifact(s) missing/empty/invalid: results/sensitivity_report.md
- **T034** — declared artifact(s) missing/empty/invalid: results/residual_stats.csv
- **T036** — declared artifact(s) missing/empty/invalid: results/analysis_verdict.md
- **T037** — No documentation files were presented in `docs/`, nor any text showing the required associational framing updates per FR‑011. The claim provides no tangible artifacts to verify that the documentation was actually modified. The missing `docs/` updates must be added and shown.
