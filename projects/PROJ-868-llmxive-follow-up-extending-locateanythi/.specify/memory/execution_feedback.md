# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ (rc=1); python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true (rc=1); python -m pytest -q tests/contract/ (rc=4); 6 declared deliverable(s) absent: data/processed/dense_subset.parquet; data/processed/exclusion_log.json; data/processed/non_dense.parquet

## Failing / missing run-book commands

- python -m src.cli.run_experiment  --datasets vrsbench coco_val  --sparsity-grid global 64 32 16  --run-one-patch false  --attribution-method gradcam  --output-dir ../../data/ -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/bin/python: Error while finding module specification for 'src.cli.run_experiment' (ModuleNotFoundError: No module named 'src')

- python -m src.cli.run_experiment  --sparsity-grid global 64 32 16  --sweep-around-tipping true -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-868-llmxive-follow-up-extending-locateanythi/bin/python: Error while finding module specification for 'src.cli.run_experiment' (ModuleNotFoundError: No module named 'src')

- python -m pytest -q tests/contract/ -> rc=4

no tests ran in 0.00s

ERROR: file or directory not found: tests/contract/



## Declared deliverables still missing

- data/processed/dense_subset.parquet
- data/processed/exclusion_log.json
- data/processed/non_dense.parquet
- data/raw/coco_val.parquet
- data/raw/refcoco_plus.parquet
- data/raw/vrsbench.parquet

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `datasets` to the project's `requirements.txt` and `pip install datasets`.
- **Verified**: this loads **5000** real records with fields: image_id, file_name, width, height.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import datasets as ds
# Load COCO 2017 validation split from Hugging Face Hub
coco = ds.load_dataset("phiyodr/coco2017", split="validation")
assert hasattr(coco, "column_names"), "Dataset missing column_names"
record_count = len(coco)
print(f"RECORDS={record_count}")
required = ["image_id","file_name","width","height","annotations","bbox","category_id","iscrowd"]
# COCO dataset provides image_id, file_name, width, height, and a column "annotations" that holds bbox, category_id, iscrowd
present = [f for f in required if f in coco.column_names or (f in {"bbox","category_id","iscrowd"} and "annotations" in coco.column_names)]
print("FIELDS=" + ",".join(present))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/processed/dense_subset.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/dense_subset.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/exclusion_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/exclusion_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/non_dense.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/non_dense.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/coco_val.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/coco_val.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/refcoco_plus.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/refcoco_plus.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/raw/vrsbench.parquet` is declared but was NOT written. Scripts referencing it:
    - `code/data/download.py` — NOT invoked by the run-book
    - `code/data/preprocess.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/raw/vrsbench.parquet` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
