# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of a `projects/PROJ-116-predicting-material-stability-using-mach/` directory or any files within it was provided; thus the required project structure cannot be confirmed as created. The implementer must add the actual directory with the expected subfolders and placeholder files (e.g., `src/`, `data/`, `README.md`, etc.) to satisfy the task.
- **T003** — No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml`, `.pre-commit-config.yaml`, `black`/`isort` settings) are present in the indicated `projects/PROJ-116-predicting-material-stability-using-mach/code/` directory, nor any documentation showing the tools have been set up. The required artifacts are missing.
- **T012** — No `download_data.py` script is present, and there is no evidence of the OQMD data being fetched, filtered, or saved to the required `projects/PROJ-116-predicting-material-stability-using-mach/data/raw/` directory, nor any logged warning about sample count. The task’s core deliverable is missing.
- **T013** — declared artifact(s) missing/empty/invalid: outputs/logs/imputation_log.txt, data/processed/baseline_features.parquet
- **T014** — declared artifact(s) missing/empty/invalid: data/models/baseline_model.pkl, outputs/baseline_tuning_results.json
- **T015** — declared artifact(s) missing/empty/invalid: outputs/baseline_results.csv
- **T016** — No code, test, or updated `baseline_results.csv` was provided to demonstrate that validation now forces inclusion of predictions and metrics even when the error exceeds 0.1 eV/atom. The required artifact (e.g., a script or pipeline change with accompanying output file) is missing, so the task is not satisfied.
- **T017** — No log files or any evidence of logging dataset size, feature count, or training metrics were presented for the path `projects/PROJ-116-predicting-material-stability-using-mach/outputs/logs/`. The required artifacts are missing, so the task is not satisfied.
- **T019** — declared artifact(s) missing/empty/invalid: tests/integration/test_augmented.py
- **T020** — No code changes to `feature_engineering.py` are present, nor any generated feature matrix or files showing Voronoi coordination numbers, face areas, solid angles, or bond‑length histograms computed with pymatgen. The required artifact (the extended module and its output) is missing.
