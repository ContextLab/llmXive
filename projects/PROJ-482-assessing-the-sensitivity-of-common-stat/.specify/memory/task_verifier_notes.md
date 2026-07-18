# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T017b** — No log entry or any other artifact confirming that the ground‑truth validation routine from T013 was executed and passed (exit code 0) is present. The required evidence—a non‑empty log confirming verification of the current configuration batch—is missing, so the task is not satisfied.
- **T021b** — The `data/processed/raw_pvalues.csv` file contains only the header line and no p‑value rows, indicating that raw p‑values are not being streamed or stored. The provided `code/simulation_engine.py` excerpt shows test execution functions but no logic that writes p‑values to the CSV (or streams them in real‑time). Consequently, the required functionality is missing.
- **T021** — declared artifact(s) missing/empty/invalid: data/processed/raw_pvalues.csv, data/processed/error_counts.csv
