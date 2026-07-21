# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T019** — The repository contains a non‑empty `src/code/ingest.py`, but the required output file `data/derived/track_count.txt` is absent, and there is no evidence that `ingest_mpd` writes the track count or logs the exact “Ingestion complete: X tracks processed” message to `pipeline_log.txt`. The task’s core deliverable is therefore not satisfied.
- **T020** — The repository lacks the required `data/derived/track_count.txt` file, and the provided `src/code/ingest.py` excerpt does not contain a `validate_coverage` function implementing the 80 % coverage check. Both the needed artifact and the specified function are missing.
