# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013a** — declared artifact(s) missing/empty/invalid: data/results/flagged_pairs_count.json
- **T013b#1** — The required input file `data/processed/comparison_log.json` is missing, and the expected output `data/results/consensus_sample.json` was not created. Without these artifacts the filtering, stratified sampling, and index writing cannot have been performed.
- **T014** — The required sample file `data/results/consensus_sample.json` is absent, and the `validate_proxy_consensus` function in `code/ranker.py` is truncated and does not contain a complete implementation that loads the sample, calls a local LLM with the specified settings, and outputs the required `{"accuracy": float, "total_samples": int, "agreed": int}` schema. These missing pieces prevent the task from being genuinely fulfilled.
- **T017** — The provided `code/data_loader.py` does not show any implementation of synthetic redundancy injection or validation for the `trec-covid` dataset, nor does it write the required `data/results/trec_covid_validation.json`. Moreover, the expected JSON result file is missing from the repository. The task’s core requirements are therefore unmet.
