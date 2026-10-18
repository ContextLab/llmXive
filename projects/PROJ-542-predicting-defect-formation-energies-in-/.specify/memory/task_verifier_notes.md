# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The required output `data/raw/materials_defects.csv` does not exist, and the only execution record is the missing-key path (exit 0), so there is no evidence of a successful download, schema validation, or the ≥500-row requirement. Additionally, the script violates FR-007's missing-key requirement by exiting cleanly with code 0 instead of aborting with an error, and it queries a fabricated Materials Project endpoint (`/rest/v2/defects/query` with `X-API-KEY` header) that does not exist in the real MP API, so even a run with a valid key would fail.
- **T003** — Requested task execution failed; rerun successfully: src/featurize.py exit=2
