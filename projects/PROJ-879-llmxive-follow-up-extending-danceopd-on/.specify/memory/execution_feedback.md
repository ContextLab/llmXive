# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/utils/check_weights.py --path <path-to-weights> (rc=1); python code/models/inference.py  --dataset data/processed/teacher_routing_dataset.parquet  --split test  --models models/trained_trees/  --pilot-samples  --target-power  --output data/results/inference_results.parquet (rc=1); python code/utils/stats.py  --input data/results/inference_results.parquet  --output data/results/statistical_tests.json (rc=1); 8 declared deliverable(s) absent: data/processed/teacher_routing_dataset.parquet; data/processed/test_split.parquet; data/processed/train_split.parquet

## Failing / missing run-book commands

- python code/utils/check_weights.py --path <path-to-weights> -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/check_weights.py", line 8, in <module>
    from utils.config import get_config, get_path
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/__init__.py", line 8, in <module>
    from .metrics import ImageDataset, calculate_clip_score, calculate_fid
ImportError: cannot import name 'ImageDataset' from 'utils.metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/metrics.py)

- python code/models/inference.py  --dataset data/processed/teacher_routing_dataset.parquet  --split test  --models models/trained_trees/  --pilot-samples  --target-power  --output data/results/inference_results.parquet -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/models/inference.py", line 23, in <module>
    from utils.config import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/__init__.py", line 8, in <module>
    from .metrics import ImageDataset, calculate_clip_score, calculate_fid
ImportError: cannot import name 'ImageDataset' from 'utils.metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/metrics.py)

- python code/utils/stats.py  --input data/results/inference_results.parquet  --output data/results/statistical_tests.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/stats.py", line 20, in <module>
    from utils.config import get_config
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/__init__.py", line 8, in <module>
    from .metrics import ImageDataset, calculate_clip_score, calculate_fid
ImportError: cannot import name 'ImageDataset' from 'utils.metrics' (/home/runner/work/llmXive/llmXive/projects/PROJ-879-llmxive-follow-up-extending-danceopd-on/code/utils/metrics.py)


## Declared deliverables still missing

- data/processed/teacher_routing_dataset.parquet
- data/processed/test_split.parquet
- data/processed/train_split.parquet
- data/processed/tree_predicted_vectors.parquet
- data/raw/imagenet_samples.parquet
- data/raw/laion_samples.parquet
- data/results/data_fetch_validation.json
- data/results/fidelity_metrics_full.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/teacher_routing_dataset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/00_check_dataset_sources.py` — NOT invoked by the run-book
    - `code/00_data_extraction.py` — NOT invoked by the run-book
    - `code/00_validate_sources.py` — NOT invoked by the run-book
    - `code/01_train_trees.py` — NOT invoked by the run-book
    - `code/02_evaluate_fidelity.py` — NOT invoked by the run-book
    - `code/02_evaluate_fidelity_parallel.py` — NOT invoked by the run-book
    - `code/validate_sources.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/teacher_routing_dataset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/test_split.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/01_train_trees.py` — NOT invoked by the run-book
    - `code/030_sample_size_config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/test_split.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/train_split.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/01_train_trees.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/train_split.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/tree_predicted_vectors.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/models/expert_reinference.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/tree_predicted_vectors.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/imagenet_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/00_data_fetch.py` — NOT invoked by the run-book
    - `code/00_data_stream.py` — NOT invoked by the run-book
    - `code/00_verify_data_sources.py` — NOT invoked by the run-book
    - `code/_data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/imagenet_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/laion_samples.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/00_data_fetch.py` — NOT invoked by the run-book
    - `code/00_data_stream.py` — NOT invoked by the run-book
    - `code/00_verify_data_sources.py` — NOT invoked by the run-book
    - `code/_data_streaming.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/laion_samples.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/data_fetch_validation.json` is declared but was NOT written. Scripts referencing it:
    - `code/00_data_fetch.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/data_fetch_validation.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/fidelity_metrics_full.csv` is declared but was NOT written. Scripts referencing it:
    - `code/030_compute_fidelity_metrics.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/fidelity_metrics_full.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
