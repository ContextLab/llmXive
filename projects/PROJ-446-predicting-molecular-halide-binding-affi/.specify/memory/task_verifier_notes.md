# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `code/01_data_ingestion.py`, its execution log, and the four output files. The script uses only 3 retries (requirement is max 5) and the generated `fetch_outcome.json` omits required exclusion‑count fields and records a null PubChem status instead of the actual 400 error, so the fetch outcome is not honestly recorded. These defects prevent the task from meeting its full specification.
