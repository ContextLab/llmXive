# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The provided `main.py` excerpt shows data fetching, cleaning, and pipeline setup but contains no code that creates a JSON report, adds a `"notes"` field, or conditionally inserts the exact FR‑013 narrative string after a successful permutation test. Consequently, the required functionality is missing.
- **T017** — The provided `main.py` excerpt ends abruptly during `run_pipeline` and never shows any code that computes the absolute difference `|L* - L_phys|` or writes it to the results. Without that logic present, the required SC‑002 output is missing. The next implementer must add the calculation (using the optimal lag from `find_optimal_lag` and the physics lag from `calculate_physics_lag`) and ensure it is reported in the pipeline’s results.
