# Execution failures — fix these before the analysis can run

## ⛔ FABRICATED RESULTS — the analysis must MEASURE, not manufacture

The gate detected that your reported numbers are NOT real measurements: they are drawn from `random.*`, forced by a tautological constant, or openly labelled simulated/placeholder because the real computation could not run. Producing files full of invented numbers is WORSE than failing — it is fabrication and will never be accepted. You MUST:

1. DELETE every fabricated metric. Do NOT draw a reported value from `random.uniform`/`np.random.*`, hardcode it to match the paper's claim, or compute it from a tautological constant.
2. Run a REAL, honestly scaled-down experiment that MEASURES the actual quantity on the CPU (e.g. time a real (small) computation, count real events, compute the real statistic over real or clearly-labelled sampled INPUT data). A small REAL result beats a big fake one.
3. If the headline quantity genuinely NEEDS a GPU (it trains/runs a transformer, a diffusion model, CUDA kernels, 8-bit quantization), do NOT fake it and do NOT cripple it onto the CPU. KEEP the real GPU code (use `device="cuda"`, the real model, 8-bit if needed) but SCALE IT DOWN to fit ONE free Kaggle GPU (~16 GB VRAM, one ~9h kernel): a small/quantized model, a few-hundred-example subset, a handful of steps. The execution stage AUTO-DETECTS the GPU requirement (the CPU run fails with a CUDA error) and re-runs your SAME run-book on Kaggle's free GPU, producing a REAL (scaled) result — that is the correct path for a GPU experiment. Do NOT add a silent CPU fallback that would run a degenerate result locally (it would never offload). Never present a simulated number as a measurement.

- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic colony data with CCD dia…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic SNP data associated with…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…None:     """     Write synthetic SNP data to VCF format.…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…"""Main function to generate synthetic data."""     parser = ar…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…umentParser(description="Generate synthetic VCF and phenotype data f…”
- code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…rt_path)          print("Synthetic data generation complete.")…”
- code/01_download.py: synthetic/fake INPUT data not authorized by the spec — “…conditional fallback to synthetic data.  Requirements: - Reques…”
- code/01_download.py: synthetic/fake INPUT data not authorized by the spec — “…"""     Executes the synthetic data generation script as a f…”

## ⚠ RUN-BOOK / CLI MISMATCH — the quickstart calls the script with the wrong arguments

These commands did not crash on a code bug — the script's own argparse REJECTED the arguments the quickstart passed (it required flags the quickstart omitted, or the quickstart passed flags the script never declared). Re-running the identical command can NEVER pass, and editing the script's logic will NOT help: the run-book command and the script's CLI have DRIFTED. Reconcile them — either change the quickstart command to match the script's real usage, OR change the script's argparse to accept the quickstart's arguments (whichever is correct for the analysis). The script's REAL usage is shown so you can see the exact gap:

- run-book command: `python code/04_ml_validation.py`
  - script usage: `04_ml_validation.py [-h] --gwas GWAS --pheno PHENO --geno GENO`
  - argparse error: `04_ml_validation.py: error: the following arguments are required: --gwas, --pheno, --geno`

The analysis code was EXECUTED end-to-end (per quickstart.md) and FAILED. The project cannot reach research_complete until the run-book runs cleanly AND produces its declared data/figure artifacts. Fix the ROOT CAUSE of each failure below — do not stub, do not fake outputs, do not mark a task done until its script actually runs and writes its real output.

**Summary**: 17 fabricated/simulated-result signal(s) — results are not real measurements: code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic colony data with CCD dia…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…[str, Any]]:     """     Generate synthetic SNP data associated with…”; code/00_generate_synthetic_data.py: synthetic/fake INPUT data not authorized by the spec — “…None:     """     Write synthetic SNP data to VCF format.…”; 3 command(s) failed: python code/01_download.py (rc=1); python code/04_ml_validation.py (rc=2); python code/05_annotation.py (rc=1); 4 declared deliverable(s) absent: data/interim/gwas_raw.tsv; data/processed/annotated_snps.tsv; data/processed/gwas_results_fdr.tsv

## Failing / missing run-book commands

- python code/01_download.py -> rc=1
    Checking SSL verification for https://www.ncbi.nlm.nih.gov/bioproject/PRJNA566029...
Fetching data for BioProject PRJNA566029...

Error fetching BioProject summary: 404 Client Error: Not Found for url: https://www.ncbi.nlm.nih.gov/bioproject/summary/PRJNA566029?format=json
Error fetching data: 404 Client Error: Not Found for url: https://www.ncbi.nlm.nih.gov/bioproject/summary/PRJNA566029?format=json
HALTING: Data fetch failed.
- python code/04_ml_validation.py -> rc=2
    usage: 04_ml_validation.py [-h] --gwas GWAS --pheno PHENO --geno GENO
                           [--output-dir OUTPUT_DIR]
04_ml_validation.py: error: the following arguments are required: --gwas, --pheno, --geno
- python code/05_annotation.py -> rc=1
    Error: GWAS results file not found: data/processed/gwas_results_fdr.tsv

## Declared deliverables still missing

- data/interim/gwas_raw.tsv
- data/processed/annotated_snps.tsv
- data/processed/gwas_results_fdr.tsv
- data/processed/threshold_sensitivity_report.tsv

## Declared deliverables NOT produced — make the run-book produce them

Every command may exit 0 yet a declared data/figure file is still absent. Fix the producing script to WRITE it to the exact declared path, and ensure that script is INVOKED by the quickstart run-book (you may edit quickstart.md to add the command).

- `data/interim/gwas_raw.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/threshold_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/interim/gwas_raw.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/annotated_snps.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05_annotation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/annotated_snps.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/gwas_results_fdr.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/05_annotation.py` — IS a run-book command
  Make ONE of these WRITE `data/processed/gwas_results_fdr.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.
- `data/processed/threshold_sensitivity_report.tsv` is declared but was NOT written. Scripts referencing it:
    - `code/utils/threshold_sensitivity.py` — NOT invoked by the run-book
  Make ONE of these WRITE `data/processed/threshold_sensitivity_report.tsv` to that EXACT path. If its producing script is not a run-book command, ADD `python code/<script>.py` to quickstart.md so the run-book invokes it.

## ⚠ CROSS-SCRIPT DATA CONTRACT — make the PRODUCER write what consumers read

One or more failures are DATA-SCHEMA mismatches BETWEEN scripts that exchange a file: a CONSUMER requires column/key names (or a file) that the PRODUCER did not write. The traceback you saw shows only the CONSUMER's EXPECTATION — never the producer's ACTUAL output — which is why this keeps failing. Below is the REAL schema each producer wrote on disk (read from the actual file) versus what the consumers require. Pick ONE canonical schema and make the **PRODUCER** write exactly the columns/keys the consumers read (preferred when one producer feeds several consumers), editing the producer IN PLACE. Do NOT fake or stub the data.

**This list is CUMULATIVE across every fix round** — keep satisfying a contract you already fixed while you fix the rest; do not drop a column merely because it is absent from this round's traceback.

### `data/processed/gwas_results_fdr.tsv`

This file is MISSING — it was never written, so every consumer of it fails as a CASCADE. Its producer is `code/05_annotation.py`; that script failed earlier this run (fix ITS failure first) or is not in the run-book. Make the producer run cleanly and WRITE `data/processed/gwas_results_fdr.tsv`; do NOT edit the cascade-victim consumers in isolation — they clear once the producer writes the file.
Consumers waiting on it: `code/05_annotation.py`.
