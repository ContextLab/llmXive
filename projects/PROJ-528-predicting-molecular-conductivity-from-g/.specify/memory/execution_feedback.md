# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 1 command(s) failed: python code/main.py (rc=1); 8 declared deliverable(s) absent: data/processed/analysis_summary.json; data/processed/corr_plot_top5.png; data/processed/descriptors.csv

## Failing / missing run-book commands

- python code/main.py -> rc=1
    Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/main.py", line 21, in <module>
    from code.run_sensitivity_analysis import main as run_sensitivity
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/run_sensitivity_analysis.py", line 11, in <module>
    from code.analysis import run_sensitivity_analysis, main as analysis_main
ImportError: cannot import name 'run_sensitivity_analysis' from 'code.analysis' (/home/runner/work/llmXive/llmXive/projects/PROJ-528-predicting-molecular-conductivity-from-g/code/analysis.py)

## Declared deliverables still missing

- data/processed/analysis_summary.json
- data/processed/corr_plot_top5.png
- data/processed/descriptors.csv
- data/processed/descriptors_base.csv
- data/processed/feature_importance.csv
- data/processed/model_results.json
- data/processed/sensitivity_analysis.json
- data/raw/smiles.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **5000** real records with fields: smiles.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import itertools
from datasets import load_dataset

ds = load_dataset("sagawa/pubchem-10m-canonicalized", split="train", streaming=True)
# Sample a manageable number of records
sample = list(itertools.islice(ds, 5000))
print(f"RECORDS={len(sample)}")
if sample:
    fields = sample[0].keys()
    print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/analysis_summary.json` is declared but was NOT written. Scripts referencing it:
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/run_validation_task.py` — NOT invoked by the run-book
    - `code/run_analysis_summary.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/analysis_summary.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/corr_plot_top5.png` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/corr_plot_top5.png` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_cross_validation.py` — NOT invoked by the run-book
    - `code/run_descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/run_validation_task.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/descriptors_base.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_descriptors.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/descriptors_base.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/feature_importance.csv` is declared but was NOT written. Scripts referencing it:
    - `code/save_analysis_outputs.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/plot_top_features.py` — NOT invoked by the run-book
    - `code/plotting.py` — NOT invoked by the run-book
    - `code/analysis_summary.py` — NOT invoked by the run-book
    - `code/feature_importance.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/feature_importance.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/model_results.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/run_analysis.py` — NOT invoked by the run-book
    - `code/run_validation_task.py` — NOT invoked by the run-book
    - `code/run_training.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/run_huckel_vif_loop.py` — NOT invoked by the run-book
    - `code/train_models.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/model_results.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/sensitivity_analysis.json` is declared but was NOT written. Scripts referencing it:
    - `code/main.py` — IS a run-book command
    - `code/sensitivity_analysis.py` — NOT invoked by the run-book
    - `code/save_model_results.py` — NOT invoked by the run-book
    - `code/run_sensitivity_analysis.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/sensitivity_analysis.json` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/raw/smiles.csv` is declared but was NOT written. Scripts referencing it:
    - `code/run_descriptor_pipeline.py` — NOT invoked by the run-book
    - `code/main.py` — IS a run-book command
    - `code/model_training.py` — NOT invoked by the run-book
    - `code/vif_iterative_retrain.py` — NOT invoked by the run-book
    - `code/outlier_sensitivity.py` — NOT invoked by the run-book
    - `code/run_training.py` — NOT invoked by the run-book
    - `code/models.py` — NOT invoked by the run-book
    - `code/config.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/smiles.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
