# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/pipelines/run_baseline.py --seed 42 --additional-seeds 123,456,789,101 --batch-size 8 (rc=1); python code/pipelines/run_conditioned.py --seed --epochs 15 (rc=1); python code/pipelines/run_analysis.py (rc=1); 7 declared deliverable(s) absent: data/artifacts/data_availability_gap_report.json; data/artifacts/data_integrity_report.json; data/artifacts/gpu_tuned_baselines.csv

## Failing / missing run-book commands

- python code/pipelines/run_baseline.py --seed 42 --additional-seeds 123,456,789,101 --batch-size 8 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_baseline.py", line 27, in <module>
    from config import CONFIG, get_data_path, get_processed_path
ImportError: cannot import name 'CONFIG' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/config.py)
- python code/pipelines/run_conditioned.py --seed --epochs 15 -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_conditioned.py", line 8, in <module>
    from models.trainer import create_trainer, Trainer
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/models/__init__.py", line 12, in <module>
    from models.projection import MLPProjection, AttentionProjection, create_projection_model
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/models/projection.py", line 10, in <module>
    class MLPProjection(nn.Module, ProjectionModel):
  File "<frozen abc>", line 106, in __new__
TypeError: Cannot create a consistent method resolution
order (MRO) for bases Module, ProjectionModel
- python code/pipelines/run_analysis.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/run_analysis.py", line 23, in <module>
    from utils.logging import setup_logging, get_logger, log_info, log_error, log_critical
ImportError: cannot import name 'setup_logging' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/utils/logging.py)
- python code/pipelines/update_state.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/pipelines/update_state.py", line 22, in <module>
    from utils.logging import setup_logging, get_logger, log_info, log_error, log_debug
ImportError: cannot import name 'setup_logging' from 'utils.logging' (/home/runner/work/llmXive/llmXive/projects/PROJ-823-llmxive-follow-up-extending-multabench-b/code/utils/logging.py)

## Declared deliverables still missing

- data/artifacts/data_availability_gap_report.json
- data/artifacts/data_integrity_report.json
- data/artifacts/gpu_tuned_baselines.csv
- data/artifacts/gpu_tuned_scalars.json
- data/artifacts/runtime_report.json
- data/processed/metadata_stats_summary.csv
- data/processed/normalized_tabular_features.parquet

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/artifacts/data_availability_gap_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/fdr_correction.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/validate_baselines.py` — NOT invoked by the run-book
    - `code/pipelines/run_fdr_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/data_availability_gap_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/data_integrity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/fdr_correction.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/validate_baselines.py` — NOT invoked by the run-book
    - `code/pipelines/verify_data_integrity.py` — NOT invoked by the run-book
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/pipelines/run_fdr_correction.py` — NOT invoked by the run-book
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/data_integrity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/gpu_tuned_baselines.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/validate_baselines.py` — NOT invoked by the run-book
    - `code/pipelines/extract_baseline_scalars.py` — NOT invoked by the run-book
    - `code/pipelines/run_t_test.py` — NOT invoked by the run-book
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/pipelines/run_analysis.py` — IS a run-book command
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/gpu_tuned_baselines.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/gpu_tuned_scalars.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/extract_baseline_scalars.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/gpu_tuned_scalars.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/artifacts/runtime_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/archive_artifacts.py` — NOT invoked by the run-book
    - `code/pipelines/run_optimized_pipeline.py` — NOT invoked by the run-book
    - `code/pipelines/review_final_validation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/artifacts/runtime_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/metadata_stats_summary.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/edge_case_processor.py` — NOT invoked by the run-book
    - `code/analysis/correlation_analysis.py` — NOT invoked by the run-book
    - `code/analysis/metadata_stats.py` — NOT invoked by the run-book
    - `code/pipelines/run_integration_test.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/aggregate_metadata_subset.py` — NOT invoked by the run-book
    - `code/pipelines/aggregate_metadata_stats.py` — NOT invoked by the run-book
    - `code/pipelines/verify_data_integrity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/metadata_stats_summary.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/normalized_tabular_features.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/models/trainer.py` — NOT invoked by the run-book
    - `code/pipelines/update_state.py` — IS a run-book command
    - `code/pipelines/normalize_tabular.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/normalized_tabular_features.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
