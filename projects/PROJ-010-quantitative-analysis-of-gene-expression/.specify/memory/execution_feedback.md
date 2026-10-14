# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5; python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json; python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv; 1 command(s) failed: python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad (rc=1)

## Failing / missing run-book commands

- python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad -> rc=1

            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/code/data_pipeline.py", line 81, in _highly_variable_genes
    sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat_v3")
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/legacy_api_wrap/__init__.py", line 88, in fn_compatible
    return fn(*args_all, **kw)
           ^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/scanpy/preprocessing/_highly_variable_genes.py", line 701, in highly_variable_genes
    return _highly_variable_genes_seurat_v3(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/scanpy/preprocessing/_highly_variable_genes.py", line 74, in _highly_variable_genes_seurat_v3
    raise ImportError(msg) from e
ImportError: Please install skmisc package via `pip install --user scikit-misc

- python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/network_inference/infer_grn.py': [Errno 2] No such file or directory

- python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/enrichment.py': [Errno 2] No such file or directory

- python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/validate.py': [Errno 2] No such file or directory


## ✅ VERIFIED REAL DATA SOURCE — use THIS in the data loader

Do NOT invent or guess a download URL/API (a hallucinated endpoint will 404). A real source was discovered AND verified by actually loading real data from it:

- **Install**: add `scanpy` to the project's `requirements.txt` and `pip install scanpy`.
- **Verified**: this loads **2700** real records with fields: cell_id, gene_id, raw_count.
- **Working access recipe** (this EXACT code was executed and returned real data — base the loader on it):

```python
import scanpy as sc

adata = sc.datasets.pbmc3k()
RECORDS = adata.n_obs

fields = []
if adata.obs.index.name or adata.obs.index is not None:
    fields.append("cell_id")
if adata.var.index.name or adata.var.index is not None:
    fields.append("gene_id")
if (adata.raw is not None and getattr(adata.raw, "X", None) is not None) or getattr(adata, "X", None) is not None:
    fields.append("raw_count")
if "sample" in adata.obs.columns:
    fields.append("donor_id")
if "age" in adata.obs.columns:
    fields.append("developmental_stage")

print(f"RECORDS={RECORDS}")
print("FIELDS=" + ",".join(fields))
```

Write the loader to use this source/recipe, persist the records to the declared raw/processed data files, and DELETE any old code that fetches from a guessed website endpoint.
