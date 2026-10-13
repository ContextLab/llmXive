# Execution failures — fix these before the analysis can run

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 3 run-book script(s) missing (plan/impl path mismatch): python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5; python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json; python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv; 1 command(s) failed: python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad (rc=1)

## Failing / missing run-book commands

- python src/data_pipeline/preprocess.py --dataset fetal_brain_atlas --output data/processed/integrated_atlas.h5ad -> rc=1
armonypy: Computing initial centroids...
2026-10-13 21:08:53,855 - harmonypy - INFO - Initialization complete.
2026-10-13 21:08:53,855 INFO harmonypy: Initialization complete.
2026-10-13 21:08:53,855 - harmonypy - INFO - Iteration 1 of 10
2026-10-13 21:08:53,855 INFO harmonypy: Iteration 1 of 10
2026-10-13 21:08:53,863 - harmonypy - INFO - Converged after 1 iteration
2026-10-13 21:08:53,863 INFO harmonypy: Converged after 1 iteration
2026-10-13 21:08:53,988 INFO code.data_pipeline: Average LISI (batch='batch'): 1.000
Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/data_pipeline/preprocess.py", line 77, in <module>
    main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/data_pipeline/preprocess.py", line 70, in main
    pipeline_main()
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/code/data_pipeline.py", line 235, in main
    raise RuntimeError(f"LISI score too low ({lisi_score:.3f} < 1.2) – aborting pipeline.")
RuntimeError: LISI score too low (1.000 < 1.2) – aborting pipeline.

- python src/network_inference/infer_grn.py --input data/processed/integrated_atlas.h5ad --windows 5 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/network_inference/infer_grn.py': [Errno 2] No such file or directory

- python src/clinical_analysis/enrichment.py --networks data/processed/networks/ --risk_genes data/raw/gwas_lists.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/enrichment.py': [Errno 2] No such file or directory

- python src/clinical_analysis/validate.py --results data/processed/disorder_enrichment.csv --bulk_data data/raw/brainspan_bulk.csv -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/validate.py': [Errno 2] No such file or directory

