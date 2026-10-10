# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 4 run-book script(s) missing (plan/impl path mismatch): python code/velocity.py --input data/processed/ --output data/processed/; python code/forkpoint.py --input data/processed/ --output data/results/fork_points/; python code/validate.py --input data/results/fork_points/ --output data/results/validation/; 1 command(s) failed: python code/preprocess.py --input data/raw/ --output data/processed/ (rc=1)

## Failing / missing run-book commands

- python code/preprocess.py --input data/raw/ --output data/processed/ -> rc=1
2026-10-10 10:41:09,240 - INFO - Checking R environment...
2026-10-10 10:41:09,240 - ERROR - R executable not found in PATH. Please install R.
2026-10-10 10:41:09,240 - ERROR - R environment check failed. Aborting.


- python code/velocity.py --input data/processed/ --output data/processed/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/velocity.py': [Errno 2] No such file or directory

- python code/forkpoint.py --input data/processed/ --output data/results/fork_points/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/forkpoint.py': [Errno 2] No such file or directory

- python code/validate.py --input data/results/fork_points/ --output data/results/validation/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/validate.py': [Errno 2] No such file or directory

- python code/report.py --input data/results/validation/ --output data/results/report/ -> rc=2

/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau/code/report.py': [Errno 2] No such file or directory


## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `scanpy` to the project's `requirements.txt` and `pip install scanpy`.
- **Verified**: this loads **2700** real records with fields: gene_id, cell_barcode, raw_counts.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import scanpy as sc
# Load a built‑in example dataset (pbmc3k) which contains gene annotations and cell metadata
adata = sc.datasets.pbmc3k()
# Number of cell records
n = int(adata.n_obs)
# Determine which of the requested fields are present
fields = []
# gene identifiers
if hasattr(adata.var, 'index') and adata.var.index.dtype == object:
    fields.append('gene_id')
# gene names (symbols)
if 'gene_symbols' in adata.var.columns:
    fields.append('gene_name')
# cell barcodes (obs names)
if adata.obs_names is not None:
    fields.append('cell_barcode')
# raw counts matrix
if adata.X is not None:
    fields.append('raw_counts')
# mitochondrial percentage (commonly stored as pct_counts_mt)
if 'pct_counts_mt' in adata.obs.columns:
    fields.append('mitochondrial_percentage')
# sample identifier (may be stored as batch or sample_id)
if 'batch' in adata.obs.columns:
    fields.append('sample_id')
elif 'sample_id' in adata.obs.columns:
    fields.append('sample_id')
# condition label (e.g., treatment vs control)
if 'condition' in adata.obs.columns:
    fields.append('condition_label')
elif 'condition_label' in adata.obs.columns:
    fields.append('condition_label')
# therapy response label
if 'therapy_response' in adata.obs.columns:
    fields.append('therapy_response')
print(f"RECORDS={n}")
print(f"FIELDS={','.join(fields)}")
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
