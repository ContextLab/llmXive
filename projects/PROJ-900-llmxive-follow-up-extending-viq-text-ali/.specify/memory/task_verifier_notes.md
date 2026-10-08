# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T036** — No verification script, log, or execution output is provided; the claim that `spec.md` was checked for the required amendments cannot be confirmed from the available artifacts. The required script and its successful run output are missing.
- **T040** — The repository contains `code/verify_data_integrity.py`, but the script’s implementation is truncated and does not show any logic that writes `data/raw/checksums.json`. Moreover, the required `data/raw/checksums.json` file is absent, so the task’s verification condition is not met. The missing checksum file (and likely incomplete script) must be added for the task to be considered complete.
- **T012** — The required output files `data/results/codebook_v0.pth` and `data/results/train_log.json` are absent, and the provided `code/train.py` is incomplete (truncated) with no visible training loop, dynamic batch‑size logic, or loss‑decrease verification. The task’s deliverables are therefore not satisfied.
