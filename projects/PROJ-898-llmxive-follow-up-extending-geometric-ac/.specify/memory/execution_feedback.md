# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/data/generator.py --num-trials 300 --output data/generated/test_set.json; python code/evaluation/runner.py --test-set data/generated/test_set.json --output data/results/trial_logs.jsonl; 3 command(s) failed: python scripts/compute_reference_stats.py --input data/results/trial_logs.jsonl --output data/results/analysis_report.md (rc=1); python scripts/compute_reference_stats.py --input data/results/trial_logs.jsonl --output data/results/analysis_report.md (rc=1); python -m pytest tests/ -v (rc=2); 3 declared deliverable(s) absent: data/generated/physics_states.json; data/raw/gam_reference_stats.json; data/results/trial_log.csv

## Failing / missing run-book commands

- python scripts/compute_reference_stats.py --input data/results/trial_logs.jsonl --output data/results/analysis_report.md -> rc=1

2026-10-09 10:51:05,236 WARNING statistical_reference: Physics‑states source unavailable: Physics states file not found: data/results/trial_logs.jsonl
2026-10-09 10:51:05,236 ERROR statistical_reference: Failed to compute reference statistics: No module named 'torch'

- python code/data/generator.py --num-trials 300 --output data/generated/test_set.json -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/code/data/generator.py': [Errno 2] No such file or directory

- python code/evaluation/runner.py --test-set data/generated/test_set.json --output data/results/trial_logs.jsonl -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-898-llmxive-follow-up-extending-geometric-ac/code/evaluation/runner.py': [Errno 2] No such file or directory

- python scripts/compute_reference_stats.py --input data/results/trial_logs.jsonl --output data/results/analysis_report.md -> rc=1

2026-10-09 10:51:06,124 WARNING statistical_reference: Physics‑states source unavailable: Physics states file not found: data/results/trial_logs.jsonl
2026-10-09 10:51:06,124 ERROR statistical_reference: Failed to compute reference statistics: No module named 'torch'

- python -m pytest tests/ -v -> rc=2
ts/test_differentiable_solver.py
ERROR tests/test_directories_setup.py
ERROR tests/test_experiment_time_validator.py
ERROR tests/test_gfm_wrapper.py
ERROR tests/test_gradient_verification.py
ERROR tests/test_inference_pipeline.py
ERROR tests/test_physics_state_extractor.py - TypeError: setup_logging() got ...
ERROR tests/test_solver_profiler.py
ERROR tests/test_statistical_reference.py
ERROR tests/test_symbolic_solver.py
ERROR tests/test_symbolic_solver_infeasible.py
ERROR tests/test_t016_integration.py
ERROR tests/test_timeout_handler.py
ERROR tests/test_trial_log_schema.py
ERROR tests/test_utils.py
ERROR tests/integration/test_lint_config.py
ERROR tests/scripts/test_generate_test_set.py
ERROR tests/unit/test_config_loader.py
ERROR tests/unit/test_config_schema.py
ERROR tests/unit/test_drift_detection.py
ERROR tests/unit/test_gfm_diff.py
ERROR tests/unit/test_latent_drift_detection.py
ERROR tests/unit/test_solver_constraints.py
ERROR tests/unit/test_symbolic_solver.py
ERROR tests/unit/test_symbolic_solver_constraints.py
!!!!!!!!!!!!!!!!!!! Interrupted: 29 errors during collection !!!!!!!!!!!!!!!!!!!
======================== 1 warning, 29 errors in 1.67s =========================



## Declared deliverables still missing

- data/generated/physics_states.json
- data/raw/gam_reference_stats.json
- data/results/trial_log.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/generated/physics_states.json` is declared but was NOT written. Scripts referencing it:
    - `code/data_generation.py` — NOT invoked by the run-book
    - `code/physics_state_extractor.py` — NOT invoked by the run-book
    - `code/refactor_inference_pipeline.py` — NOT invoked by the run-book
    - `code/statistical_reference.py` — NOT invoked by the run-book
    - `scripts/compute_reference_stats.py` — IS a run-book command
    - `scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/generated/physics_states.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/gam_reference_stats.json` is declared but was NOT written. Scripts referencing it:
    - `code/statistical_reference.py` — NOT invoked by the run-book
    - `scripts/compute_reference_stats.py` — IS a run-book command
    - `scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/gam_reference_stats.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/trial_log.csv` is declared but was NOT written. Scripts referencing it:
    - `code/inference_pipeline.py` — NOT invoked by the run-book
    - `code/refactor_inference_pipeline.py` — NOT invoked by the run-book
    - `code/trial_log_schema.py` — NOT invoked by the run-book
    - `scripts/validate_quickstart.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/trial_log.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
