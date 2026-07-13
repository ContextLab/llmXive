# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T007b** — The provided `download_hcp.py` only contains code for fetching (or mocking) behavioral data; there is no visible logic that selects subjects with valid Sleep Scores nor excludes subjects whose `FD_mean` exceeds 0.3 mm. The file is truncated before any such filtering could appear, and no reference to the output of T005 is present. Implement the subject‑filtering step (e.g., a function that reads the behavioral CSV, keeps rows with non‑missing Sleep Scores and `FD_mean` ≤ 0.3, and logs excluded IDs).
