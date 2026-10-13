# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5; python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json; python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv; 2 command(s) failed: python src/data_pipeline/setup_data.py (rc=1); python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad (rc=1)

## Failing / missing run-book commands

- python src/data_pipeline/setup_data.py -> rc=1

2026-10-13 20:15:31,542 INFO __main__: GEO accession GSE131928 reachable: True
2026-10-13 20:15:31,542 INFO __main__: Downloading raw dataset from https://raw.githubusercontent.com/scverse/scanpy_usage/master/data/pbmc3k.h5ad
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/data_pipeline/setup_data.py", line 153, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/data_pipeline/setup_data.py", line 128, in main
    _download_raw_dataset(raw_path)
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/data_pipeline/setup_data.py", line 96, in _download_raw_dataset
    response.raise_for_status()
  File "/home/runner/.cache/llmxive/base-env/py311-6f1866971868/requests/models.py", line 1024, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/scverse/scanpy_usage/master/data/pbmc3k.h5ad

- python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad -> rc=1
/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/code/data_pipeline.py", line 245, in main
    adata.obsm["X_pca_harmony"] = ho.Z_corr.T
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/anndata/_core/aligned_mapping.py", line 219, in __setitem__
    value = self._validate_value(value, key)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/anndata/_core/aligned_mapping.py", line 285, in _validate_value
    return super()._validate_value(val, key)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/anndata/_core/aligned_mapping.py", line 102, in _validate_value
    raise ValueError(msg)
ValueError: Value passed for key 'X_pca_harmony' is of incorrect shape. Values of obsm must match dimensions ('obs',) of parent. Value had shape (30,) while it should have had (2700,).

- python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/network_inference/infer_grn.py': [Errno 2] No such file or directory

- python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/enrichment.py': [Errno 2] No such file or directory

- python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/validate.py': [Errno 2] No such file or directory

