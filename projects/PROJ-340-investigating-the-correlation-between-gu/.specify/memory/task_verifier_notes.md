# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T059** — The repository contains a partially‑implemented `code/main.py` with RAM‑estimation helpers, but the file is truncated (the `save_compute_strategy` function is incomplete) and there is no code that actually writes `data/metadata/compute_strategy.json`. Moreover, the required JSON output file does not exist on disk. The task’s core deliverable – generating the compute strategy JSON – is therefore missing.
- **T061** — The required `.github/workflows/analysis.yml` file does not exist in the repository, so there is no workflow definition, let alone a `kaggle-gpu` job with the specified error‑detection and re‑trigger logic. The implementer must add the missing workflow file and implement the described behavior.
