# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The repository contains `code/03_gwas.sh`, but the script is truncated (ends abruptly) and does not reliably enforce the mandatory covariates nor guarantee creation of `data/interim/gwas_raw.tsv` (the file is missing). Consequently the required output artifact is absent and the script does not fully meet the task specification.
- **T022** — The `code/04_apply_fdr.sh` script exists, but the required output file `data/processed/gwas_results_fdr.tsv` is missing, so the final artifact the task demanded was not produced. The next implementer must run the script (or otherwise generate) to create the `gwas_results_fdr.tsv` file with the merged results.
- **T075** — declared artifact(s) missing/empty/invalid: code/06_power_analysis.py
