# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011a** — The `src/data/verify_metadata.py` file exists, but the required output artifact `data/processed/metadata_verification_report.json` is missing, and the provided code snippet is truncated before any logic that would generate and write that report. Without the JSON report, the task’s core output is not produced.
- **T013** — The `src/data/batch_correction.py` file is present but its implementation is truncated and does not show the required ComBat‑seq call, geNorm selection of the 50 lowest‑M genes, CV computation, or JSON report writing. Moreover, the mandatory output file `data/manifests/batch_correction_report.json` is missing. The task’s core requirements are therefore not satisfied.
