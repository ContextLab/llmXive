# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The `state_validator.py` file exists, but the required `data/raw/golden_subset.json` does not exist, so the validator cannot actually calculate accuracy against the golden data. Additionally, the provided code snippet is truncated, leaving the core logic incomplete. The missing golden subset file must be generated (e.g., by running T015) and the full validator implementation completed.
- **T016** — No JSON report was provided; the required keys (`state_persistence_count`, `reasoning_deficit_count`, `total_failures`, `classification_confidence`) and the calculated proportion of State Persistence Errors are absent, so the task’s deliverable is missing.
- **T031** — No evidence of a `docs/` directory or an updated `quickstart.md` file was provided; without seeing the actual documentation files, we cannot confirm that the required documentation updates exist. The implementer must supply the updated docs (e.g., a non‑empty `docs/quickstart.md` reflecting the new feature).
