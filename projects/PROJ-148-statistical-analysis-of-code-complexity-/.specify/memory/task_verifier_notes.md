# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `code/data/download_gh.py` falls back to a GitHub search instead of downloading the GHTorrent Java dataset from the required AWS mirror, skips checksum verification for fallback archives, extracts whole archives (not just `*.java` files), and the run log shows only 9 successful project directories (one download failed), violating the ≥ 10 projects requirement. The script also does not abort on checksum failures as mandated.
- **T003** — Requested task execution failed; rerun successfully: code/data/label_bug_fixes.py exit=1
