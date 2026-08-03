# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019** — No `energy_samples.csv` file is present in `data/derived/`, and no output showing the required columns or the warning log is provided. The implementer must generate the CSV with the specified columns and ensure the `pot_incomplete` flag and warning behavior are correctly implemented.
- **T024** — The `code/stats.py` file contains a partially‑implemented `bin_energy_data` function that stops at a comment and never returns the described DataFrame, and the required input file `data/derived/energy_samples.csv` is absent, so the function cannot be exercised or verified. The implementation must be completed and the CSV data provided.
