# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017** — The `validation.py` file is present and contains logic to compute dielectric deviations, but the required `solvents.yaml` reference file is missing, so the code cannot actually perform the comparison. Without the lookup table the module cannot flag runs >2% deviation, violating the task’s requirement. The missing `solvents.yaml` must be added (or the code adjusted to handle its absence) for the task to be complete.
- **T034** — declared artifact(s) missing/empty/invalid: figures/regression_plot.png, data/processed/correlation_results.json
