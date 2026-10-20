# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows `data/raw/`, `data/processed/`, `results/`, `code/`, and `tests/` directories exist, but the required `logs/` folder is not present at the repository root. Adding the missing `logs/` directory will satisfy the task.
- **T002** — Checked the `requirements.txt` file (it lists exact versions for all required packages) and the install log showing those versions are installed, but there is no `installed.txt` file nor a `diff -u requirements.txt installed.txt` output proving that the installed environment matches the pinned versions as required.
- **T003** — The provided `code/seed.py` correctly sets deterministic seeds and writes its SHA‑256 hash, and `code/seed_hash.txt` matches that hash. However, there is no evidence that all pipeline scripts import `seed.py` as their first line, as required by the task. This usage requirement is unverified, so the task is not fully satisfied.
- **T004** — Requested task execution failed; rerun successfully: code/power_analysis.py exit=1
