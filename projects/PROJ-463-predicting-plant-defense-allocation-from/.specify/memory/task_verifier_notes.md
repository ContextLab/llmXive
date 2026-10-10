# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows `src/__init__.py`, `tests/__init__.py`, and the three `.gitkeep` files under `data/raw`, `data/processed`, and `data/traits`, but there is no confirmed presence of `data/manifests/.gitkeep`, `data/synthetic/.gitkeep`, nor the required flag file `data/.dir_setup_complete`. These missing files prevent the task from being fully satisfied.
- **T002** — The `requirements.txt` file is present and lists the required packages, but none of them are version‑pinned (e.g., `rpy2==...`). The task explicitly demanded a *pinned* requirements file, so the artifact does not meet the specification. Adding exact version specifiers for each listed dependency is needed.
- **T003a-fix** — The `pyproject.toml` file with `[tool.ruff]` and `[tool.black]` sections is present, but there is no provided evidence that `ruff check .` and `black --check .` were actually run and passed. Execution logs or command output confirming successful linting/formatting are required.
- **T003b-install-deps** — No artifact (e.g., a shell script, log file, or captured command output) showing that the specified `conda install …` command was run, nor any evidence that the subsequent version checks (`fastp --version`, etc.) were executed and returned exit code 0. Without such execution evidence, the task’s installation and verification requirements are not satisfied.
- **T003c-fix** — declared artifact(s) missing/empty/invalid: data/manifests/env_validation.json
- **T007-fix** — declared artifact(s) missing/empty/invalid: src/utils/setup_dirs.py
- **T037** — declared artifact(s) missing/empty/invalid: src/analysis/pathway_aggregation.py, data/processed/pathway_mappings.json, data/processed/pathway_features.csv
- **T024** — declared artifact(s) missing/empty/invalid: tests/unit/test_validation.py
- **T053** — declared artifact(s) missing/empty/invalid: src/analysis/tissue_specificity.py
- **T030** — declared artifact(s) missing/empty/invalid: src/cli/run_pipeline.py
- **T050** — declared artifact(s) missing/empty/invalid: src/analysis/sensitivity_analysis.py
- **T051** — declared artifact(s) missing/empty/invalid: src/cli/report_generator.py
