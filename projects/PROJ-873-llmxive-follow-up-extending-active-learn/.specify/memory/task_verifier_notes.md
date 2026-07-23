# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013b** — The required output file `data/results/consensus_sample.json` is missing, so the stratified sampling result was not produced. The existing `sample_config.json` is present, but without the consensus sample file the task is not fulfilled.
- **T014** — The required `data/results/consensus_sample.json` file does not exist, and the `validate_proxy_consensus` function in `code/ranker.py` is truncated and contains only a stub without any LLM invocation, model configuration, or logic to compute ground‑truth accuracy. Both the input data and the full implementation are missing.
- **T017** — The provided `code/data_loader.py` is truncated and contains no implementation of synthetic redundancy validation, similarity checking (> 0.95), or code that writes `data/results/trec_covid_validation.json`. Moreover, the required JSON result file does not exist. The task’s core requirements are therefore unmet.
