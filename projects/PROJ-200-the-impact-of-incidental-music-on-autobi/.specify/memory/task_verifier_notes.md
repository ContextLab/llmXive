# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The two contract files exist, but the `contracts/dataset.schema.yaml` defines `matched_track_id` with a quoted `"null"` type, which is not a valid JSON‑Schema null type and will cause `jsonschema` validation to fail. Moreover, the provided pytest logs error out before any contract validation runs (missing `python_levenshtein` module), so there is no evidence that the schemas actually pass validation against the spec. The task therefore remains incomplete.
- **T004** — Requested task execution failed; rerun successfully: code/data_ingestion.py exit=1
