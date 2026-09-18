# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/data/loader.py --filter-min-lines 500 --output data/filtered_swe_bench.parquet (rc=1); python code/experiments/run_baseline.py --model 1b --strategy baseline --max-instances a sufficient number of instances to ensure statistical power (rc=1); python code/experiments/run_high_fidelity.py --models b,7b --strategies baseline,tfidf,diff_aware,summarization --output data/results.csv (rc=1); 1 declared deliverable(s) absent: data/results.csv

## Failing / missing run-book commands

- python code/data/loader.py --filter-min-lines 500 --output data/filtered_swe_bench.parquet -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py", line 16, in <module>
    from config import get_data_dir, get_output_dir, set_global_seeds
ImportError: cannot import name 'get_data_dir' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config/__init__.py)
- python code/experiments/run_baseline.py --model 1b --strategy baseline --max-instances a sufficient number of instances to ensure statistical power -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py", line 22, in <module>
    from config import set_global_seeds, get_data_dir, get_output_dir, get_log_level
ImportError: cannot import name 'set_global_seeds' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config/__init__.py)
- python code/experiments/run_high_fidelity.py --models b,7b --strategies baseline,tfidf,diff_aware,summarization --output data/results.csv -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_high_fidelity.py", line 21, in <module>
    from config import set_global_seeds, get_env_var, get_model_path, get_data_dir, get_output_dir, StrategyType
ImportError: cannot import name 'set_global_seeds' from 'config' (/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/config/__init__.py)
- python code/analysis/glm_analyzer.py --input data/results.csv --output data/glm_results.json -> rc=1
    2026-09-18 11:22:47,306 - __main__ - INFO - Starting GLM analysis on data/results.csv
2026-09-18 11:22:47,306 - __main__ - ERROR - GLM analysis failed: Results file not found: data/results.csv

## Declared deliverables still missing

- data/results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/experiments/batch_executor.py` — NOT invoked by the run-book
    - `code/experiments/run_baseline.py` — IS a run-book command
    - `code/experiments/run_high_fidelity.py` — IS a run-book command
    - `code/tests/integration/test_baseline_execution.py` — NOT invoked by the run-book
    - `code/tests/unit/test_failure_classifier.py` — NOT invoked by the run-book
    - `code/tests/unit/test_glm_analyzer.py` — NOT invoked by the run-book
    - `code/analysis/glm_analyzer.py` — IS a run-book command
  Make ONE of these WRITE `data/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/results.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/tests/unit/test_glm_analyzer.py`, `code/analysis/glm_analyzer.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/results.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis/glm_analyzer.py`.
