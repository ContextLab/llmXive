# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T009a** — No `research.md` file containing the required text was provided; the verification command (`grep -q "K_IC formula" research.md && grep -q "base_value" research.md`) cannot succeed because the artifact is missing, so the methodology section and formula are not demonstrated. The implementer must add a `research.md` with Section 3.2 that includes the explicit K_IC formula and the terms “base_value”, “alpha”, “beta”, etc.
- **T005** — The repository contains `code/data/synthetic_gen.py`, but the required output files are absent: `data/raw/metadata.json` does not exist and there are no PNG images in `data/raw/` to meet the ≥ 2,000 count. Consequently the task’s verification conditions are not satisfied.
