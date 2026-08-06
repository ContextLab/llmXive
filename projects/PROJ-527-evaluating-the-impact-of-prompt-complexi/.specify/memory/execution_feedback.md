# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/main.py; python projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/main.py --sample-size 10; 2 declared deliverable(s) absent: data/processed/prompt_variants.parquet; data/results/execution_outcomes.csv

## Failing / missing run-book commands

- python projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/main.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/main.py': [Errno 2] No such file or directory
- python projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/main.py --sample-size 10 -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi/code/main.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/processed/prompt_variants.parquet
- data/results/execution_outcomes.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **164** real records with fields: task_id, prompt, canonical_solution, test, entry_point.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import json, sys
from datasets import load_dataset
# Load the HumanEval benchmark from Hugging Face Hub
ds = load_dataset('openai/openai_humaneval', split='test')
print(f'RECORDS={len(ds)}')
# Print the available field names (columns)
print('FIELDS=' + ','.join(ds.column_names))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/prompt_variants.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/collinearity_check.py` — NOT invoked by the run-book
    - `code/analysis/manual_review_flagger.py` — NOT invoked by the run-book
    - `code/analysis/structural_redundancy_check.py` — NOT invoked by the run-book
    - `code/execution/write_results.py` — NOT invoked by the run-book
    - `code/utils/versioning.py` — NOT invoked by the run-book
    - `code/prompts/tokenizer.py` — NOT invoked by the run-book
    - `code/prompts/generator.py` — NOT invoked by the run-book
    - `code/data/storage.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/prompt_variants.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/results/execution_outcomes.csv` is declared but was NOT written. Scripts referencing it:
    - `code/analysis/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/analysis/viz.py` — NOT invoked by the run-book
    - `code/analysis/stats.py` — NOT invoked by the run-book
    - `code/analysis/aggregator.py` — NOT invoked by the run-book
    - `code/execution/write_results.py` — NOT invoked by the run-book
    - `code/utils/versioning.py` — NOT invoked by the run-book
    - `code/llm/update_version_after_generation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/results/execution_outcomes.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
