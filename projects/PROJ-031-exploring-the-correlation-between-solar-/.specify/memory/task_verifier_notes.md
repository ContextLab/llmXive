# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T067** — The `code/analysis.py` does define a `calculate_mdes` function, but the `power_analysis` routine never checks for N < 30 nor writes a “Power Limitation” entry to `results/metrics.json`. Moreover, the required `results/metrics.json` file does not exist at all. The task’s conditions are therefore not satisfied.
- **T068** — No code, configuration, or unit‑test files were presented that demonstrate the threshold‑sensitivity analysis (T034b) is restricted to the 2021‑2023 hold‑out set, nor is there a unit test confirming the data split enforcement. The required artifact (the implemented logic and its verification test) is missing.
