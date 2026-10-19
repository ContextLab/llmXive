# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `docs/quickstart.md`, `code/ingestion/fetch_data.py`, `code/modeling/train.py`, `code/modeling/evaluate.py`, and the absence of any `logs/pipeline.log` or execution evidence. The quickstart doc is present but its AFLOWlib URL description is garbled, and the ingestion script catches AFLOW fetch failures instead of raising as required. No log file or run output is provided to prove the documented command sequence executes end‑to‑end and records the source URLs. The pipeline therefore does not demonstrably meet the provenance and strict‑failure requirements.
- **T002** — Requested task execution failed; rerun successfully: code/ingestion/fetch_data.py exit=1
