# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required project directories (`src/`, `tests/`, `data/`, `output/`) is provided; the claim lacks any artifact showing that these folders exist or contain files. The implementer must create and show the directory structure to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or related scripts) were found in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied.
- **T006** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — The provided `src/data/validate.py` is truncated (the `validate_data` function ends mid‑line) and cannot fully perform validation, and the required `dataset.schema.yaml` file is missing, so the script cannot actually check raw data against a schema as the task demands. The implementation must be completed and the schema file supplied.
- **T009** — declared artifact(s) missing/empty/invalid: src/utils/plots.py
- **T015** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T018** — declared artifact(s) missing/empty/invalid: src/data/clean.py
- **T026** — No `output/signals.csv` file or its contents were presented; the required columns (`soc`, `ror`, `ror_ci_lower`, `ror_ci_upper`, `prr`, `prr_ci_lower`, `prr_ci_upper`, `ic`, `ic_ci_lower`, `ic_ci_upper`, `p_adj`, `signal_flag`) are not demonstrated, so the task’s deliverable is missing.
- **T027** — declared artifact(s) missing/empty/invalid: src/analysis/sensitivity.py
- **T028** — No `output/sensitivity_analysis.csv` file or its contents were presented; therefore the required delta‑metrics CSV with the specified columns does not exist in the provided evidence. The task remains unfinished.
- **T030** — Both required artifacts (`src/analysis/temporal.py` and `tests/unit/test_temporal.py`) are missing from the repository, so no unit test or implementation exists to verify the weekly aggregation logic. The task is therefore not satisfied.
