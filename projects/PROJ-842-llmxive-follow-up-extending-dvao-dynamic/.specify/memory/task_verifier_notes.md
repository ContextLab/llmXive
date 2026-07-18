# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree, `__init__.py` files, or `.gitkeep` placeholders are presented as evidence; the required project structure and files are not shown, so the claim cannot be verified. The implementer must provide the actual filesystem layout containing the specified directories and files.
- **T019** — declared artifact(s) missing/empty/invalid: src/derivation/sample_complexity.py
- **T021** — declared artifact(s) missing/empty/invalid: src/analysis/stats.py
- **T027** — The required file `src/derivation/sample_complexity.py` does not exist, so there is no code to verify that it correctly inverts variance to a sample complexity bound. The task cannot be considered completed until this file is present and contains the appropriate implementation.
- **T028** — No mathematical derivation, code, synthetic environment generator, heuristic implementation, or statistical validation artifacts were supplied; the claim lacks any concrete output to verify that the explicit i.i.d. noise assumption was logged in the derivation output. The required documents and scripts are missing.
- **T034** — No code, documentation, or test results were provided showing logic that detects when the number of objectives N exceeds 50 and then degrades the state‑space size or applies sampling. Without any artifact demonstrating this edge‑case handling, the task requirement is not met.
- **T035** — declared artifact(s) missing/empty/invalid: data/processed/empirical_results.json
- **T037** — No code, script, logs, or test output demonstrating that the synthetic MDP generator produces identical environments when initialized with the same random seed is present. The required artifact proving deterministic MDP generation with seeded random states is missing.
- **T038** — declared artifact(s) missing/empty/invalid: src/analysis/stats.py
- **T039** — No code, logs, or test output were supplied that demonstrate the implementation of the stability check or that the ratio of heuristic to full‑batch variance stays within [0.9, 1.1] for at least 95 % of steps. The claim lacks any concrete artifact to verify the requirement.
