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

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 16 fabricated/simulated-result signal(s) — results are not real measurements: code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…""" Synthetic Data Generator for Honeybee C…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…Validation.  This module generates deterministic synthetic VCF and Phenotype data f…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic colony data with CCD dia…”; 7 run-book script(s) missing (plan/impl path mismatch): python code/06_power_analysis.py; python code/08_apply_fdr.py; python code/09_threshold_sensitivity.py; 3 command(s) failed: python code/02_harmonize_phenotypes.py (rc=2); python code/04_filter_snps.py (rc=2); python code/05_collinearity_diag.py (rc=1); 2 declared deliverable(s) absent: data/interim/gwas_raw.tsv; data/processed/gwas_results_fdr.tsv

## Failing / missing run-book commands

- python code/02_harmonize_phenotypes.py -> rc=2
    usage: 02_harmonize_phenotypes.py [-h] --input INPUT [--output-dir OUTPUT_DIR]
02_harmonize_phenotypes.py: error: the following arguments are required: --input
- python code/04_filter_snps.py -> rc=2
    usage: 04_filter_snps.py [-h] --input-bed INPUT_BED --input-pheno INPUT_PHENO
                         [--output-prefix OUTPUT_PREFIX]
                         [--r2-threshold R2_THRESHOLD]
04_filter_snps.py: error: the following arguments are required: --input-bed, --input-pheno
- python code/05_collinearity_diag.py -> rc=1
    Error: Input file not found: data/processed/phenotypes_cleaned.pheno
- python code/06_power_analysis.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/06_power_analysis.py': [Errno 2] No such file or directory
- python code/08_apply_fdr.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/08_apply_fdr.py': [Errno 2] No such file or directory
- python code/09_threshold_sensitivity.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/09_threshold_sensitivity.py': [Errno 2] No such file or directory
- python code/10_lasso_validation.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/10_lasso_validation.py': [Errno 2] No such file or directory
- python code/11_prs_and_lr_test.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/11_prs_and_lr_test.py': [Errno 2] No such file or directory
- python code/12_annotate_genes.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/12_annotate_genes.py': [Errno 2] No such file or directory
- python code/13_format_results.py -> rc=2 [script missing]
    /home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/.venv/bin/python: can't open file '/home/runner/work/llmXive/llmXive/projects/PROJ-207-identifying-genetic-markers-associated-w/code/13_format_results.py': [Errno 2] No such file or directory

## Declared deliverables still missing

- data/interim/gwas_raw.tsv
- data/processed/gwas_results_fdr.tsv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/gwas_raw.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/03_gwas.py` — NOT invoked by the run-book
    - `code/utils/fdr_correction.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/gwas_raw.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gwas_results_fdr.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05_annotation.py` — NOT invoked by the run-book
    - `code/utils/threshold_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/gwas_results_fdr.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/gwas_results_fdr.tsv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/05_annotation.py`, `code/utils/threshold_sensitivity.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/gwas_results_fdr.tsv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/05_annotation.py`, `code/utils/threshold_sensitivity.py`.
