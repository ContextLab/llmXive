# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 run-book script(s) missing (plan/impl path mismatch): python code/cli/run_pipeline.py --subset-size 85 --max-permutations 10000; 3 declared deliverable(s) absent: data/processed/dynamic_scores.json; data/processed/static_scores.json; data/results/correlation_results.csv

## Failing / missing run-book commands

- python code/cli/run_pipeline.py --subset-size 85 --max-permutations 10000 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-861-llmxive-follow-up-extending-appo-agentic/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/cli/run_pipeline.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/processed/dynamic_scores.json
- data/processed/static_scores.json
- data/results/correlation_results.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **6914** real records with fields: system_prompt, question, answer, short_answer, generation, messages.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets, json, sys

ds = datasets.load_dataset("thesven/gsm8k-reasoning", split="train")
records = len(ds)
fields = list(ds[0].keys())
print(f"RECORDS={records}")
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/dynamic_scores.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/dynamic_score/generate_output.py` — NOT invoked by the run-book
    - `code/dynamic_score/run_appo.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/dynamic_scores.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/static_scores.json` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/correlation.py` — NOT invoked by the run-book
    - `code/dynamic_score/generate_output.py` — NOT invoked by the run-book
    - `code/static_score/batch_processor.py` — NOT invoked by the run-book
    - `code/static_score/compute.py` — NOT invoked by the run-book
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/static_scores.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/results/correlation_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/correlation_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
