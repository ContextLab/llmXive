# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019** — No `data/derived/energy_samples.csv` file, no `artifacts/energy_samples.hash`, and no evidence of schema validation or warning logs were provided; thus the required output and verification artifacts are missing.
- **T024** — The provided `code/stats.py` does not read `data/derived/energy_samples.csv` nor raise the required `FileNotFoundError` with the exact message; it instead expects a DataFrame argument and raises a custom `StatsError`. It also lacks the explicit check for a “test_” filename prefix and any handling of a T029 flag. Additionally, the required `data/derived/energy_samples.csv` file is absent. These omissions mean the task’s specifications are not met.
