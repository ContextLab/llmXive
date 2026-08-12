# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T027** — The required artifact `.github/workflows/test_reproducibility.yml` does not exist in the repository, so the integration test cannot be verified. The task’s core deliverable is missing.
- **T031b** — The repository contains `code/utils/verify_pii_removal.py`, but the required data file `data/interaction_logs/anonymized_logs.csv` is missing, so the script cannot actually scan any logs. Additionally, the displayed portion of the script is truncated and does not show the logic that checks whether `data/consent/` is excluded from VCS history, leaving it unclear whether that part of the requirement is fulfilled. Both the missing CSV and the incomplete script cause the task to be incomplete.
