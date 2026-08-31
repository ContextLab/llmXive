# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T090** — The required output file `data/processed/cue_intensity_weights.json` does not exist, so the weighting schemes are not actually stored as specified. The script defines the correct weights, but without the JSON file the task’s deliverable is missing.
- **T014** — The required output file `data/processed/counterbalanced_trials.csv` does not exist, and the provided `code/02_counterbalance.py` is truncated and contains errors (e.g., undefined variable `stim`, no CSV writing logic). Consequently the script cannot generate the required counterbalanced trials, and the contract test cannot be satisfied.
- **T015** — The repository lacks the required `data/processed/presentation_orders.csv` file, and the provided `code/03_random_order.py` is incomplete (the `save_orders` function is cut off and no command‑line handling or entry‑point is shown). Consequently the script cannot generate the promised CSV, so the task’s requirement is not met.
