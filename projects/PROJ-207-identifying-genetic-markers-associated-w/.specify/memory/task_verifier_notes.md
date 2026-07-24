# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T022** — The `code/04_apply_fdr.sh` script exists, but the required input file `data/interim/gwas_raw.tsv` is missing, and the script never invokes PLINK nor creates the expected output `data/processed/gwas_results_fdr.tsv`. Consequently the pipeline cannot actually perform the FDR correction as specified. The missing input and output files must be provided and the script should pipe PLINK results to the Python correction utility.
