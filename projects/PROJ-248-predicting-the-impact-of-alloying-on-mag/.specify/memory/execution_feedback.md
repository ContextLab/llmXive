# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python code/download_datasets.py`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 command(s) failed: python code/download_datasets.py (rc=1); python -m src.models.train  --targets saturation_magnetization curie_temperature  --datasets oqmd mp  --output_dir artifacts  --log_dir logs (rc=1); python -m src.cli.predict  --model_saturation artifacts/model_saturation.pkl  --model_curie artifacts/model_curie.pkl  --input example_alloy.json  --output prediction.json (rc=1); 1 declared deliverable(s) absent: data/raw_oqmd.csv

## Failing / missing run-book commands

- python code/download_datasets.py -> rc=1
^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/lib/python3.11/site-packages/datasets/load.py", line 1667, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/lib/python3.11/site-packages/datasets/load.py", line 1290, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/lib/python3.11/site-packages/datasets/load.py", line 1176, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/lib/python3.11/site-packages/datasets/load.py", line 1134, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'materialsproject/mp' doesn't exist on the Hub or cannot be accessed.

- python -m src.models.train  --targets saturation_magnetization curie_temperature  --datasets oqmd mp  --output_dir artifacts  --log_dir logs -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/bin/python: Error while finding module specification for 'src.models.train' (ModuleNotFoundError: No module named 'src')

- python -m src.cli.predict  --model_saturation artifacts/model_saturation.pkl  --model_curie artifacts/model_curie.pkl  --input example_alloy.json  --output prediction.json -> rc=1

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-248-predicting-the-impact-of-alloying-on-mag/bin/python: Error while finding module specification for 'src.cli.predict' (ModuleNotFoundError: No module named 'src')


## Declared deliverables still missing

- data/raw_oqmd.csv

## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `matminer` to the project's `requirements.txt` and `pip install matminer`.
- **Verified**: this loads **1181** real records with fields: material_id, formula, nsites, space_group, volume, structure, elastic_anisotropy, G_Reuss, G_VRH, G_Voigt, K_Reuss, K_VRH, K_Voigt, poisson_ratio, compliance_tensor, elastic_tensor, elastic_tensor_original, cif, kpoint_density, poscar.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import pandas as pd
from matminer.datasets import load_dataset, get_available_datasets

# Choose a dataset known to exist in matminer
dataset_name = "elastic_tensor_2015"
if dataset_name not in get_available_datasets():
    raise ValueError(f"Dataset '{dataset_name}' is not available. Available datasets: {get_available_datasets()}")

df = load_dataset(dataset_name)

print(f"RECORDS={len(df)}")
if len(df) > 0:
    print("FIELDS=" + ",".join(df.columns.tolist()))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/raw_oqmd.csv` is declared but was NOT written. Scripts referencing it:
    - `code/download_datasets.py` — IS a run-book command
  Make ONE of these WRITE `data/raw_oqmd.csv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
