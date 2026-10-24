# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — The provided `src/utils/verify_requirements.py` checks for a top‑level `requirements.txt` instead of the required `code/requirements.txt`, so it does not fulfill the core requirement of verifying the pinned requirements file in the `code/` directory. The script must be updated to reference `repo_root / "code" / "requirements.txt"` (and optionally handle its hash) to satisfy the task.
