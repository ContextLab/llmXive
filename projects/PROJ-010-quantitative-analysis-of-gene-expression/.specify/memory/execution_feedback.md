# Execution failures — fix these before the analysis can run

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python src/data_pipeline/preprocess.py  --dataset human_mtg  --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA"  --output data/processed/integrated_atlas.h5ad  --seed 42`
  - script usage: `preprocess.py [-h] [--dataset DATASET] [--output OUTPUT]`
  - argparse error: `preprocess.py: error: unrecognized arguments: --dataset_url https://huggingface.co/datasets/BICCN/human_mtg_scRNA --seed 42`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 8 run-book script(s) missing (plan/impl path mismatch): python src/network_inference/pseudotime.py  --input data/processed/integrated_atlas.h5ad  --output data/processed/pseudotime.h5ad  --marker_genes NEUROD6,GFAP,MAP2  --min_correlation 0.6  --seed 42; python src/network_inference/infer_grn.py  --input data/processed/pseudotime.h5ad  --windows 5  --hub_degree_threshold 10  --hub_top_n 20  --output_dir data/processed/networks  --seed 42; python src/network_inference/motif_enrichment.py  --network_dir data/processed/networks  --output_dir data/processed/networks_motif  --motif_threshold 0.05  --seed 42; 1 command(s) failed: python src/data_pipeline/preprocess.py  --dataset human_mtg  --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA"  --output data/processed/integrated_atlas.h5ad  --seed 42 (rc=2)

## Failing / missing run-book commands

- python src/data_pipeline/preprocess.py  --dataset human_mtg  --dataset_url "https://huggingface.co/datasets/BICCN/human_mtg_scRNA"  --output data/processed/integrated_atlas.h5ad  --seed 42 -> rc=2

usage: preprocess.py [-h] [--dataset DATASET] [--output OUTPUT]
preprocess.py: error: unrecognized arguments: --dataset_url https://huggingface.co/datasets/BICCN/human_mtg_scRNA --seed 42

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

