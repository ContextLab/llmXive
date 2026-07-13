# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The provided `model_metrics.py` does not actually load the `Salesforce/codegen-350M-mono` model in 8‑bit quantization nor compute real perplexities; it merely checks for the presence of `bitsandbytes` and returns a constant dummy value. Hence the core requirement of loading the model and computing genuine perplexity is unmet.
- **T021** — The repository contains `code/main.py`, but the required output files `data/processed/clone_metrics.csv` and `data/processed/perplexity_scores.csv` are absent, and the script does not implement any logic to join the two metric sets into those CSVs. Consequently the pipeline does not fulfill the stated requirement.
