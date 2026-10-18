# Execution failures — fix these before the analysis can run

## ⚠ DATA-UNAVAILABLE failure — switch to a REAL, REACHABLE data source

These commands failed because the external dataset is NOT reachable AS WRITTEN on the free CI runner: a Hugging Face dataset that was renamed (canonical names like `openai_humaneval` now require a `namespace/name`), had its loading script removed (`datasets` >= 3 dropped `trust_remote_code` script datasets), is gated, or needs network the runner lacks. RE-TRYING THE DOWNLOAD AS-IS WILL NEVER SUCCEED. Fix it with REAL data, in this order:

1. CORRECT the source: use the dataset's current canonical id (`namespace/name`), a public mirror, or a direct file URL, and stream / download only a SMALL REAL SAMPLE (the first N rows, one split, a few files). A verified real source may be injected below — use it.
2. If that exact dataset is truly unreachable, switch to a DIFFERENT but genuinely-public dataset that supports the SAME analysis/metric, and say so honestly in the README.
3. Do NOT substitute synthetic / fake / hand-built data for the real dataset. A result computed on invented data is NOT a real finding and is REJECTED by the deterministic fabrication gate — swapping in synthetic data is the single most common reason this loop never converges. The ONLY exception is a project whose OWN research question is about synthetic / simulated data (its idea says so).
4. If, after the above, NO real data can be obtained on the CI runner, do NOT fabricate a result: leave the run to FAIL so it escalates honestly (model-tier escalation / re-plan), rather than producing a fake finding.

- `python src/data_pipeline/setup_data.py  --seed 42  --output_dir data/raw`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 run-book script(s) missing (plan/impl path mismatch): python src/network_inference/pseudotime.py  --input data/processed/integrated_atlas.h5ad  --output data/processed/pseudotime.h5ad  --marker_genes NEUROD6,GFAP,MAP2  --min_correlation 0.6  --seed 42; python src/network_inference/infer_grn.py  --input data/processed/pseudotime.h5ad  --windows 5  --hub_degree_threshold 10  --hub_top_n 20  --output_dir data/processed/networks  --seed 42; python src/network_inference/motif_enrichment.py  --network_dir data/processed/networks  --output_dir data/processed/networks_motif  --motif_threshold 0.05  --seed 42; 2 command(s) failed: python src/data_pipeline/setup_data.py  --seed 42  --output_dir data/raw (rc=1); python src/data_pipeline/preprocess.py  --dataset human_mtg  --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA"  --output data/processed/integrated_atlas.h5ad  --seed 42 (rc=1)

## Failing / missing run-book commands

- python src/data_pipeline/setup_data.py  --seed 42  --output_dir data/raw -> rc=1
^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/datasets/load.py", line 1667, in load_dataset
    builder_instance = load_dataset_builder(
                       ^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/datasets/load.py", line 1290, in load_dataset_builder
    dataset_module = dataset_module_factory(
                     ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/datasets/load.py", line 1176, in dataset_module_factory
    raise e1 from None
  File "/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/lib/python3.11/site-packages/datasets/load.py", line 1134, in dataset_module_factory
    raise DatasetNotFoundError(f"Dataset '{path}' doesn't exist on the Hub or cannot be accessed.") from e
datasets.exceptions.DatasetNotFoundError: Dataset 'scanpy/10x_5k_human_pbmc' doesn't exist on the Hub or cannot be accessed.

- python src/data_pipeline/preprocess.py  --dataset human_mtg  --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA"  --output data/processed/integrated_atlas.h5ad  --seed 42 -> rc=1

Traceback (most recent call last):
  File "/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/data_pipeline/preprocess.py", line 36, in <module>
    from code.data_pipeline import calculate_lisi, calculate_stage_variance
ImportError: cannot import name 'calculate_lisi' from 'code.data_pipeline' (/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/code/data_pipeline/__init__.py)

- python src/network_inference/pseudotime.py  --input data/processed/integrated_atlas.h5ad  --output data/processed/pseudotime.h5ad  --marker_genes NEUROD6,GFAP,MAP2  --min_correlation 0.6  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/network_inference/pseudotime.py': [Errno 2] No such file or directory

- python src/network_inference/infer_grn.py  --input data/processed/pseudotime.h5ad  --windows 5  --hub_degree_threshold 10  --hub_top_n 20  --output_dir data/processed/networks  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/network_inference/infer_grn.py': [Errno 2] No such file or directory

- python src/network_inference/motif_enrichment.py  --network_dir data/processed/networks  --output_dir data/processed/networks_motif  --motif_threshold 0.05  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/network_inference/motif_enrichment.py': [Errno 2] No such file or directory

- python src/network_inference/rewiring.py  --network_dir data/processed/networks_motif  --thresholds 0.01 0.05 0.1  --normalize zscore  --output data/processed/rewiring_events.csv  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/network_inference/rewiring.py': [Errno 2] No such file or directory

- python src/clinical_analysis/gwas_mapping.py  --gwas_source "https://www.ebi.ac.uk/gwas/"  --output data/processed/gwas_mapped.json -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/gwas_mapping.py': [Errno 2] No such file or directory

- python src/clinical_analysis/enrichment.py  --rewiring data/processed/rewiring_events.csv  --gwas data/processed/gwas_mapped.json  --background matched  --iterations 5000  --fdr_method bh  --output data/processed/disorder_enrichment.csv  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/enrichment.py': [Errno 2] No such file or directory

- python src/clinical_analysis/validation.py  --rewiring data/processed/rewiring_events.csv  --independent_sc "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE147457"  --bulk_brainspan "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE36520"  --output data/processed/disorder_enrichment.csv  --seed 42 -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/clinical_analysis/validation.py': [Errno 2] No such file or directory

- python src/utils/plotting.py  --networks data/processed/networks_motif  --rewiring data/processed/rewiring_events.csv  --enrichment data/processed/disorder_enrichment.csv  --output_dir results/ -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-010-quantitative-analysis-of-gene-expression/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-010-quantitative-analysis-of-gene-expression/src/utils/plotting.py': [Errno 2] No such file or directory

