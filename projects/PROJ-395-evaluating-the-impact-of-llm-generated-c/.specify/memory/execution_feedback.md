# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download.py --dataset humaneval --output data/raw/`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 command(s) failed: python code/download.py --dataset humaneval --output data/raw/ (rc=1); python code/generate.py --model tinyllama-1.1b --n-50 --output data/processed/llm_solutions.csv (rc=1); python code/profile.py --input data/processed/ --runs 3 --output data/processed/memory_measurements.csv (rc=1); 1 declared deliverable(s) absent: data/processed/memory_measurements.csv

## Failing / missing run-book commands

- python code/download.py --dataset humaneval --output data/raw/ -> rc=1
Downloading mbpp split=test...
Error: Failed to download dataset mbpp: Invalid HF URI 'hf://datasets/mbpp@4bb6404fdc6cacfda99d4ac4205087b89d32030c/.huggingface.yaml'. Repository id must be 'namespace/name', got 'mbpp'.

`trust_remote_code` is not supported anymore.
Please check that the Hugging Face dataset 'mbpp' isn't based on a loading script and remove `trust_remote_code`.
If the dataset is based on a loading script, please ask the dataset author to remove it and convert it to a standard format like Parquet.
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.

- python code/generate.py --model tinyllama-1.1b --n-50 --output data/processed/llm_solutions.csv -> rc=1
ile "/home/runner/work/llmXive/llmXive/projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/code/.venv/lib/python3.11/site-packages/transformers/utils/import_utils.py", line 2677, in __getattr__
    raise ModuleNotFoundError(import_error_message) from e
ModuleNotFoundError: Could not import module 'GenerationMixin'. Are this object's requirements defined correctly? Set the logging verbosity to DEBUG for the original import error.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/code/generate.py", line 35, in <module>
    from transformers import AutoModelForCausalLM, AutoTokenizer
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/code/.venv/lib/python3.11/site-packages/transformers/utils/import_utils.py", line 2677, in __getattr__
    raise ModuleNotFoundError(import_error_message) from e
ModuleNotFoundError: Could not import module 'AutoModelForCausalLM'. Are this object's requirements defined correctly? Set the logging verbosity to DEBUG for the original import error.

- python code/profile.py --input data/processed/ --runs 3 --output data/processed/memory_measurements.csv -> rc=1
Error: Input file not found: /home/runner/work/llmXive/llmXive/projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/data/processed/generated_solutions.json


- python code/analyze.py --measurements data/processed/memory_measurements.csv --features data/processed/code_features.csv --output data/processed/statistical_report.json -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/code/analyze.py", line 9, in <module>
    from statsmodels.stats.stattools import owen_vif
ImportError: cannot import name 'owen_vif' from 'statsmodels.stats.stattools' (/home/runner/work/llmXive/llmXive/projects/PROJ-395-evaluating-the-impact-of-llm-generated-c/code/.venv/lib/python3.11/site-packages/statsmodels/stats/stattools.py)


## Declared deliverables still missing

- data/processed/memory_measurements.csv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/memory_measurements.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analyze.py` — IS a run-book command
    - `code/config.py` — NOT invoked by the run-book
    - `code/generate_report.py` — NOT invoked by the run-book
    - `code/profile.py` — IS a run-book command
    - `code/utils.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/memory_measurements.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
