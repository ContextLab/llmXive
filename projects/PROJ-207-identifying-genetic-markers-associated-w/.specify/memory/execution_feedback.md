# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Honeybee C…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…Validation.  This module generates deterministic synthetic VCF and Phenotype data f…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic colony data with CCD dia…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic SNP data associated with…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…None:     """     Write synthetic SNP data to VCF format.      VCF…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…ON report validating the synthetic data against FR-011.     """…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Main entry point for synthetic data generation."""     parse…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Generate synthetic VCF and Phenotype data f…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/02_harmonize_phenotypes.py`
  - script usage: `02_harmonize_phenotypes.py [-h] --input INPUT [--output-dir OUTPUT_DIR]`
  - argparse error: `02_harmonize_phenotypes.py: error: the following arguments are required: --input`
- run-book command: `python code/04_filter_snps.py`
  - script usage: `04_filter_snps.py [-h] --input-bed INPUT_BED --input-pheno INPUT_PHENO`
  - argparse error: `04_filter_snps.py: error: the following arguments are required: --input-bed, --input-pheno`
- run-book command: `python code/09_threshold_sensitivity.py`
  - script usage: `09_threshold_sensitivity.py [-h] --input INPUT [--output OUTPUT]`
  - argparse error: `09_threshold_sensitivity.py: error: the following arguments are required: --input`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 19 fabricated/simulated-result signal(s) — results are not real measurements: code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Honeybee C…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…Validation.  This module generates deterministic synthetic VCF and Phenotype data f…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic colony data with CCD dia…”; 8 run-book script(s) missing (plan/impl path mismatch): bash code/01_download_data.sh; bash code/03_align_and_call.sh; python code/06_power_analysis.py; 5 command(s) failed: python code/02_harmonize_phenotypes.py (rc=2); python code/04_filter_snps.py (rc=2); python code/05_collinearity_diag.py (rc=1); 7 declared deliverable(s) absent: data/interim/gwas_raw.tsv; data/processed/annotation_results.tsv; data/processed/collinearity_report.json

## Failing / missing run-book commands

- bash code/01_download_data.sh -> rc=-1

shell script must be an existing project-local .sh file
- python code/02_harmonize_phenotypes.py -> rc=2

usage: 02_harmonize_phenotypes.py [-h] --input INPUT [--output-dir OUTPUT_DIR]
02_harmonize_phenotypes.py: error: the following arguments are required: --input

- bash code/03_align_and_call.sh -> rc=-1

shell script must be an existing project-local .sh file
- python code/04_filter_snps.py -> rc=2

usage: 04_filter_snps.py [-h] --input-bed INPUT_BED --input-pheno INPUT_PHENO
                         [--output-prefix OUTPUT_PREFIX]
                         [--r2-threshold R2_THRESHOLD]
04_filter_snps.py: error: the following arguments are required: --input-bed, --input-pheno

- python code/05_collinearity_diag.py -> rc=1
Loading phenotype data from data/processed/phenotypes_cleaned.pheno...
ERROR: Input file not found: data/processed/phenotypes_cleaned.pheno


- python code/06_power_analysis.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-207-identifying-genetic-markers-associated-w/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/06_power_analysis.py': [Errno 2] No such file or directory

- bash code/07_gwas_plink.sh -> rc=-1

shell script must be an existing project-local .sh file
- python code/08_apply_fdr.py -> rc=1
Loading raw GWAS results from: data/interim/gwas_raw.tsv

ERROR: Raw GWAS results file not found: data/interim/gwas_raw.tsv. Ensure code/03_gwas.py (or equivalent) has been run successfully.

- python code/09_threshold_sensitivity.py -> rc=2

usage: 09_threshold_sensitivity.py [-h] --input INPUT [--output OUTPUT]
                                   [--min-threshold MIN_THRESHOLD]
                                   [--max-threshold MAX_THRESHOLD]
                                   [--step STEP]
09_threshold_sensitivity.py: error: the following arguments are required: --input

- python code/10_lasso_validation.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-207-identifying-genetic-markers-associated-w/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/10_lasso_validation.py': [Errno 2] No such file or directory

- python code/11_prs_and_lr_test.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-207-identifying-genetic-markers-associated-w/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/11_prs_and_lr_test.py': [Errno 2] No such file or directory

- python code/12_annotate_genes.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-207-identifying-genetic-markers-associated-w/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/12_annotate_genes.py': [Errno 2] No such file or directory

- python code/13_format_results.py -> rc=2

/home/runner/work/llmXive/llmXive/.llmxive-venvs/PROJ-207-identifying-genetic-markers-associated-w/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/13_format_results.py': [Errno 2] No such file or directory


## Declared deliverables still missing

- data/interim/gwas_raw.tsv
- data/processed/annotation_results.tsv
- data/processed/collinearity_report.json
- data/processed/gwas_results_fdr.tsv
- data/processed/ncbi_fetch_log.json
- data/processed/ncbi_metadata.json
- data/processed/threshold_sensitivity.json

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/gwas_raw.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/03_gwas.py` — NOT invoked by the run-book
    - `code/08_apply_fdr.py` — IS a run-book command
    - `code/utils/fdr_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/gwas_raw.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/annotation_results.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05_annotation.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/annotation_results.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/collinearity_report.json` is declared but was NOT written. Scripts referencing it:
    - `code/04_ml_validation.py` — NOT invoked by the run-book
    - `code/05_collinearity_diag.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/collinearity_report.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gwas_results_fdr.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05_annotation.py` — NOT invoked by the run-book
    - `code/08_apply_fdr.py` — IS a run-book command
    - `code/utils/threshold_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/gwas_results_fdr.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ncbi_fetch_log.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_download.py` — NOT invoked by the run-book
    - `code/01_download_metadata.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/ncbi_fetch_log.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/ncbi_metadata.json` is declared but was NOT written. Scripts referencing it:
    - `code/01_download_metadata.py` — NOT invoked by the run-book
    - `code/02_harmonize_phenotypes.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/ncbi_metadata.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_sensitivity.json` is declared but was NOT written. Scripts referencing it:
    - `code/05_profile_pipeline.py` — NOT invoked by the run-book
    - `code/09_threshold_sensitivity.py` — IS a run-book command
    - `code/utils/threshold_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_sensitivity.json` to that EXACT path. If its producing script is not a run-book command, ADD `python <source-path>.py` to quickstart.md so the run-book invokes it.
