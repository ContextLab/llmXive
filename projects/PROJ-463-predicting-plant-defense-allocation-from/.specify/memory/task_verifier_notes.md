# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011a** — The repository contains `src/data/verify_metadata.py`, but the file is truncated and does not show logic that writes `data/processed/metadata_verification_report.json`. Moreover, the required JSON report is missing from the filesystem, indicating the implementation does not fulfill the output requirement. The next implementer should complete the script (including verification of tissue, herbivore type, and replicates) and ensure it always creates the `metadata_verification_report.json` file in `data/processed`.
