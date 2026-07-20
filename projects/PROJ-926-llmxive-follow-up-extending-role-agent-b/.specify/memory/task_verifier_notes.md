# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The repository contains a `tests/integration/test_baseline_generation.py` file, but it is truncated, calls a function (`generate_baseline_failures`) instead of executing the required `generate_baseline.py` script, and the expected output `data/raw/baseline_failures.json` does not exist. Consequently the integration test does not meet the stated constraint and cannot verify the real generation step.
