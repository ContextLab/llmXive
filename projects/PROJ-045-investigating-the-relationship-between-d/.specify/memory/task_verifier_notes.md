# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The required `data/processed/validation_log.txt` file does not exist, and the `validate.py` implementation (as shown) does not write JSON‑line entries with the exact schema (`violation_type`, `composition_id`, `distance`, `ideal_range`). Instead it creates a dict with different keys (`value`, `threshold`). Consequently the task’s output and format requirements are not met.
