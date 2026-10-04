# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T031** — No file `generate_partitions.py` with a new docstring is present; the claim provides no code or documentation showing the required explanation of the generating function \(\prod_{p\in\mathbb{P}}(1+q^{p})\) and its distinction from \(\prod (1-q^{k})^{-1}\). The task’s artifact (the updated script) is missing.
- **T016b** — The required `data/processed/features.csv` file is missing, so the validation tests cannot run on real data. Moreover, the test suite does not contain a function named `test_features_non_null` as the task explicitly requests; it only provides separate column‑specific checks. Both the missing CSV and the absent correctly‑named test mean the task’s requirement is not satisfied.
