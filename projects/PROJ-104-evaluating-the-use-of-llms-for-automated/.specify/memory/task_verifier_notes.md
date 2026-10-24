# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The quick‑start guide and `run_pipeline.py` correctly implement the smoke‑test and produce `data/generated/phi3-mini/sample_test.txt`, but the required test suite (`tests/test_quickstart.py` or equivalent) is missing, so there is no evidence that the command runs under 30 s or that the pytest verification passes. Adding the missing test file and execution timing evidence is needed.
- **T002** — The `code/power_analysis.py` script exists and writes a markdown report, but it only simulates a single medium effect using Cohen’s d = 0.5 (not the required Cohen’s f = 0.25) and does not vary effect sizes as the task specifies. Consequently the core requirement of “simulate paired precision scores … under varying effect sizes” is not fulfilled.
