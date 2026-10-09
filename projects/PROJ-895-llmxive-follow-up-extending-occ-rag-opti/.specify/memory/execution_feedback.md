# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 2 run-book script(s) missing (plan/impl path mismatch): python code/utils/verify_checksums.py; python code/_prune_model.py --retention-pct 50; 2 command(s) failed: python code/01_sensitivity_analysis.py --sample-size '[variable]' --masking-unit head (rc=1); python code/04_statistical_validation.py (rc=1); 4 declared deliverable(s) absent: data/processed/original_faithfulness_scores.csv; data/processed/pruned_faithfulness_scores.csv; data/processed/sensitivity_results.csv

## Failing / missing run-book commands

- python code/utils/verify_checksums.py -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/utils/verify_checksums.py': [Errno 2] No such file or directory

- python code/01_sensitivity_analysis.py --sample-size '[variable]' --masking-unit head -> rc=1

INFO:__main__:Starting sensitivity analysis with delta faithfulness calculation
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/01_sensitivity_analysis.py", line 332, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/01_sensitivity_analysis.py", line 289, in main
    validate_config(config)
TypeError: validate_config() takes 0 positional arguments but 1 was given

- python code/_prune_model.py --retention-pct 50 -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/_prune_model.py': [Errno 2] No such file or directory

- python code/04_statistical_validation.py -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/04_statistical_validation.py", line 300, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/code/04_statistical_validation.py", line 262, in main
    validate_config(config)
TypeError: validate_config() takes 0 positional arguments but 1 was given


## Declared deliverables still missing

- data/processed/original_faithfulness_scores.csv
- data/processed/pruned_faithfulness_scores.csv
- data/processed/sensitivity_results.csv
- data/processed/statistical_validation_report.json

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **105257** real records with fields: id, question, answer, type, level, supporting_facts, context.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
from datasets import load_dataset

dataset_dict = load_dataset("hotpotqa/hotpot_qa", "fullwiki")
total_records = sum(len(split) for split in dataset_dict.values())
print(f"RECORDS={total_records}")

first_split = next(iter(dataset_dict.values()))
print("FIELDS=" + ",".join(first_split.column_names))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/original_faithfulness_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/original_faithfulness_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/pruned_faithfulness_scores.csv` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/pruned_faithfulness_scores.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_results.csv` is declared but was NOT written. Scripts referencing it:
    - `code/01_sensitivity_analysis.py` — IS a run-book command
    - `code/02_prune_model.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_results.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/statistical_validation_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_statistical_validation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/statistical_validation_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
