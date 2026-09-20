# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — No evidence of the required `specs/001-the-influence-of-visual-complexity-on-im/amendment-001.md` file or an updated `spec.md` that references the amendment or marks FR‑003 as “Amended” was provided. Both artifacts are missing, so the ratification task is not satisfied.
- **T002** — The required file `projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/requirements.txt` does not exist, and the existing `code/requirements.txt` contains a different package list, not the specified specification excerpt. The task’s core artifact is missing.
- **T027a** — declared artifact(s) missing/empty/invalid: data/processed/counterbalance_assignment.csv
- **T027b** — No evidence of a `logs/counterbalance_strategy.log` file was provided, nor any content showing the required seed and split‑ratio values. The implementer must create the log file and ensure it records the specific counterbalancing assignment strategy, including those details.
- **T032** — The repository lacks the required `data/processed/complexity_scores.csv` and the resulting `data/results/pca_variance.json` files, so the script cannot actually read metrics or produce the expected output. Moreover, the `pca.py` implementation raises `FileNotFoundError` and `ValueError`, violating the “do not raise ValueError or halt pipeline” rule, and the `main` function is truncated, never writing the warning‑status JSON. The task therefore remains unfinished.
- **T034** — declared artifact(s) missing/empty/invalid: data/results/permutation_results.json
- **T035** — No code, data, or visualizations implementing the Threshold and LOIO sensitivity analyses were provided; the claim lacks any concrete artifact demonstrating that the required analysis was performed.
