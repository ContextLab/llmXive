# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The provided `code/main.py` excerpt shows data‑quality logging but contains no code that creates a JSON report, adds a `"notes"` field, or conditionally inserts the exact FR‑013 narrative after a successful permutation test. Consequently the required functionality is not present. The file must be extended to generate the JSON report, detect successful execution of the permutation test (FR‑005), and append the exact note string to the `"notes"` field only in that case.
- **T016** — The repository contains a `main.py` with a `log_quality_warnings` function, but the shown code never writes the `report` to `data/processed/quality_log.json` (no `json.dump` or file write) and the expected `quality_log.json` file is absent. Consequently the required JSON log artifact is missing.
