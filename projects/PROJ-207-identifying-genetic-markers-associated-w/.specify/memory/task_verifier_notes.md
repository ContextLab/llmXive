# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The script `code/03_gwas.sh` exists but is truncated and never actually creates or writes `data/interim/gwas_raw.tsv`; the required conversion/renaming step is missing. Consequently the artifact does not reliably produce the specified raw association output file.
- **T022** — The script `code/04_apply_fdr.sh` exists, but it does not invoke PLINK nor pipe its output to the Python utility as required, and the expected input file `data/interim/gwas_raw.tsv` and output file `data/processed/gwas_results_fdr.tsv` are missing. The task’s core requirement is therefore not satisfied.
