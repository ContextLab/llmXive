# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The stored hash does not match the file: `code/seed.py`'s actual SHA-256 is `a9186b31...` but `code/seed_hash.txt` contains `a937a4aa...`, so the task's own verification (`diff -u current_hash.txt code/seed_hash.txt`) fails. Additionally, the recorded test run (`tests/test_seed_import.py`, exit 1) shows `code/create_dirs.py` does not import `seed` as its first functional line, violating the requirement that all pipeline scripts import the module first.
- **T004** — Requested task execution failed; rerun successfully: code/power_analysis.py exit=1
