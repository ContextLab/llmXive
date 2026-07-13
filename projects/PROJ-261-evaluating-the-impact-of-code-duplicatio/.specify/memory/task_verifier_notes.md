# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T021** — The provided `code/main.py` exists, but it never creates or writes the required `data/processed/clone_metrics.csv` and `data/processed/perplexity_scores.csv` files, nor does it join the two metric sets as the task specifies. The `clone_metrics.csv` file is missing entirely, indicating the pipeline does not produce the expected outputs. The implementation must generate both CSVs (including a combined/joined version) in the `data/processed` directory.
