# Execution failures — fix these before the analysis can run

## ⚠ REGRESSIONS — your last fix BROKE these (they passed before)

These commands were NOT failing in the previous round and ARE failing now — your last edit broke previously-working code. REVERT or correct whatever change broke each one BEFORE touching anything else; do not trade one passing script for another (that oscillation is what burns the fix-round budget toward escalation):

- `python -c "import datasets, transformers, statsmodels, pandas, sentence_transformers; print('OK')"`
- `python analysis/metrics.py --input data/intermediate/classified_results.jsonl --output data/results.csv`
- `python code/analysis/failure_classifier.py --input 'data/intermediate/*.jsonl' --output data/intermediate/classified_results.jsonl`
- `python code/experiments/run_baseline.py --model 1B --strategy baseline --output data/intermediate/baseline_run.jsonl`
- `python experiments/run_scaling.py --model 7B --strategy baseline --output data/intermediate/hf_run_7b_baseline.jsonl`
- `python experiments/run_scaling.py --model 7B --strategy tfidf --output data/intermediate/hf_run_7b_tfidf.jsonl`
- `python experiments/run_strategies.py --model 1B --strategy diff_aware --output data/intermediate/hf_run_1b_diff.jsonl`
- `python experiments/run_strategies.py --model 1B --strategy summarization --output data/intermediate/hf_run_1b_summ.jsonl`
- `python experiments/run_strategies.py --model 1B --strategy tfidf --output data/intermediate/hf_run_1b_tfidf.jsonl`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 6 run-book script(s) missing (plan/impl path mismatch): python experiments/run_strategies.py --model 1B --strategy tfidf --output data/intermediate/hf_run_1b_tfidf.jsonl; python experiments/run_strategies.py --model 1B --strategy diff_aware --output data/intermediate/hf_run_1b_diff.jsonl; python experiments/run_strategies.py --model 1B --strategy summarization --output data/intermediate/hf_run_1b_summ.jsonl; 3 command(s) failed: python code/experiments/run_baseline.py --model 1B --strategy baseline --output data/intermediate/baseline_run.jsonl (rc=1); python code/analysis/failure_classifier.py --input 'data/intermediate/*.jsonl' --output data/intermediate/classified_results.jsonl (rc=1); python code/analysis/glm_analyzer.py --input data/results.csv --output data/glm_results.json (rc=1); 2 declared deliverable(s) absent: data/filtered_swe_bench_v1.parquet; data/results.csv

## Failing / missing run-book commands

- python -c "import datasets, transformers, statsmodels, pandas, sentence_transformers; print('OK')" -> rc=1
    Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'sentence_transformers'
- python code/experiments/run_baseline.py --model 1B --strategy baseline --output data/intermediate/baseline_run.jsonl -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/experiments/run_baseline.py", line 11, in <module>
    from data.loader import ClawSweBenchLoader
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/__init__.py", line 2, in <module>
    from .loader import ClawSweBenchLoader, filter_dataset, write_parquet_and_checksum
ImportError: cannot import name 'filter_dataset' from 'data.loader' (/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/data/loader.py)
- python experiments/run_strategies.py --model 1B --strategy tfidf --output data/intermediate/hf_run_1b_tfidf.jsonl -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_strategies.py': [Errno 2] No such file or directory
- python experiments/run_strategies.py --model 1B --strategy diff_aware --output data/intermediate/hf_run_1b_diff.jsonl -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_strategies.py': [Errno 2] No such file or directory
- python experiments/run_strategies.py --model 1B --strategy summarization --output data/intermediate/hf_run_1b_summ.jsonl -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_strategies.py': [Errno 2] No such file or directory
- python experiments/run_scaling.py --model 7B --strategy baseline --output data/intermediate/hf_run_7b_baseline.jsonl -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_scaling.py': [Errno 2] No such file or directory
- python experiments/run_scaling.py --model 7B --strategy tfidf --output data/intermediate/hf_run_7b_tfidf.jsonl -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/experiments/run_scaling.py': [Errno 2] No such file or directory
- python code/analysis/failure_classifier.py --input 'data/intermediate/*.jsonl' --output data/intermediate/classified_results.jsonl -> rc=1
    2026-10-03 07:30:16,707 - __main__ - ERROR - File not found: Input file not found: data/intermediate/*.jsonl
- python analysis/metrics.py --input data/intermediate/classified_results.jsonl --output data/results.csv -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben/analysis/metrics.py': [Errno 2] No such file or directory
- python code/analysis/glm_analyzer.py --input data/results.csv --output data/glm_results.json -> rc=1
    2026-10-03 07:30:18,938 - __main__ - ERROR - GLM analysis failed: Results file not found: data/results.csv

## Declared deliverables still missing

- data/filtered_swe_bench_v1.parquet
- data/results.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/filtered_swe_bench_v1.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/checksum_recorder.py` — NOT invoked by the run-book
    - `code/analysis/threshold_validator.py` — NOT invoked by the run-book
    - `code/analysis/construct_validity.py` — NOT invoked by the run-book
    - `code/experiments/run_high_fidelity.py` — NOT invoked by the run-book
    - `code/experiments/run_7b_experiments.py` — NOT invoked by the run-book
    - `code/experiments/run_baseline.py` — IS a run-book command
  Make ONE of these WRITE `data/filtered_swe_bench_v1.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/config.py` — NOT invoked by the run-book
    - `code/data/context_processors.py` — NOT invoked by the run-book
    - `code/tests/integration/test_baseline_execution.py` — NOT invoked by the run-book
    - `code/tests/unit/test_failure_classifier.py` — NOT invoked by the run-book
    - `code/tests/unit/test_glm_analyzer.py` — NOT invoked by the run-book
    - `code/analysis/merge_results.py` — NOT invoked by the run-book
    - `code/analysis/apply_failure_classification.py` — NOT invoked by the run-book
    - `code/analysis/checksum_recorder.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/results.csv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/tests/unit/test_glm_analyzer.py`, `code/analysis/merge_results.py`, `code/analysis/checksum_recorder.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/results.csv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/analysis/merge_results.py`, `code/analysis/checksum_recorder.py`, `code/analysis/merge_results_runner.py`.
