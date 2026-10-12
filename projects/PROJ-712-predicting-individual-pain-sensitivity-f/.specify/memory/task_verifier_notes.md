# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — `code/utils.py` exists and the tests pass, and seed pinning plus the `artifacts/log.txt` logger are genuinely implemented. However, the task explicitly requires `record_artifact_hash(filepath)` to "compute a SHA‑256 hash and **return it**," but the implemented function returns `None` (it only writes the hash to a YAML state file); the hash value is never returned to the caller. Fix `record_artifact_hash` to return the computed SHA‑256 hex digest (e.g., `return hash_val`) while optionally keeping the YAML recording.
