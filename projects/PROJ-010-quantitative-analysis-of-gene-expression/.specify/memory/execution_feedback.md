# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5; python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json; python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv; 1 command(s) failed: python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad (rc=1)

## Failing / missing run-book commands

- python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad -> rc=1
port main as pipeline_main
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/code/data_pipeline.py", line 5, in <module>
    import scanpy as sc
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/scanpy/__init__.py", line 27, in <module>
    from . import datasets, logging, queries, external, get, metrics, experimental
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/scanpy/metrics/__init__.py", line 3, in <module>
    from ._morans_i import morans_i
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/scanpy/metrics/_morans_i.py", line 131, in <module>
    W: np.float_,
       ^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/numpy/__init__.py", line 400, in __getattr__
    raise AttributeError(
AttributeError: `np.float_` was removed in the NumPy 2.0 release. Use `np.float64` instead.

- python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/network_inference/infer_grn.py': [Errno 2] No such file or directory

- python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/enrichment.py': [Errno 2] No such file or directory

- python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/validate.py': [Errno 2] No such file or directory

