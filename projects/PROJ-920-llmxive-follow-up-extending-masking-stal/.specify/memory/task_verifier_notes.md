# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T011** — Checked `code/generate_trajectories.py` and the generated `data/raw/trajectories.jsonl`. The script builds a full list of 500 trajectories in memory and writes it with `json.dump`, not line‑by‑line streaming as required, and its default output is `trajectories.json` (JSON array) rather than a true JSON‑Lines file. Consequently the key “stream each trajectory to disk line‑by‑line to keep RAM ≤ 2 GB” is not satisfied.
- **T012** — Requested task execution failed; rerun successfully: code/validate_trajectories.py exit=1
