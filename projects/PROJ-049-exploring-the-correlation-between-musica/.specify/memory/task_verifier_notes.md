# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows the required folders `data/raw`, `data/processed`, `results`, `code`, and `tests` exist, but the `logs/` directory is missing entirely, and all listed directories are under the project sub‑folder `projects/PROJ-049‑exploring‑the‑correlation‑between‑musica` rather than at the repository root as the task specifies.
- **T003** — The provided `code/seed.py` correctly sets deterministic seeds and writes its SHA‑256 hash, and `code/seed_hash.txt` matches that hash. However, there is no evidence that all pipeline scripts import `seed.py` as their first line, as required by the task. This usage requirement is unverified, so the task is not fully satisfied.
- **T004** — Requested task execution failed; rerun successfully: code/power_analysis.py exit=1
