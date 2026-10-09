# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001.1** — No evidence of the requested directory tree (e.g., a listing or screenshot showing the `projects/PROJ-455-predicting-plant-stress-resilience-from-` hierarchy) is provided, so we cannot confirm that the `mkdir -p …` command was actually executed and the directories exist. The required artifact is missing.
- **T001.2** — No script, command output, or log file is provided that runs `ls` on the paths from T001.1 and checks the exit codes. Consequently, there is no evidence that the required directories were actually verified to exist.
- **T003** — The repository contains a `pyproject.toml` with Black configuration, but there is no `.flake8` file present, which is required to complete the linting setup. The missing `.flake8` configuration must be added for the task to be fully satisfied.
- **T004.2** — The schema file exists but its contents do not match the required fields. It defines r2, rmse, mean_absolute_error, cv_folds, training_time_seconds, and mode, while the task demanded `model_type`, `metric_name`, `metric_value`, `feature_importance` (list), `p_value` (nullable), `validation_method`, and `seed_used`. Those required properties are missing, so the task is not fulfilled.
- **T037.1** — declared artifact(s) missing/empty/invalid: tests/benchmark/test_scalability.py
