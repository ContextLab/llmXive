# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `requirements.txt` exists, but it is located inside the project subdirectory (`projects/PROJ-320-evaluating-the-impact-of-code-generation/requirements.txt`) rather than at the repository root as required, and there is no evidence (e.g., installation logs) that `pip install -r requirements.txt` succeeds on a fresh runner. Both location and successful install verification are missing.
- **T008** — Requested task execution failed; rerun successfully: tests/unit/test_checksum.py exit=1
- **T015a/T015c Secondary detector (`code/data/entropy_detector.py`) that computes a simple token‑entropy score over the PR diff and adds `entropy_score` (0‑1).  The detector is used later for validation (FR‑007).** — declared artifact(s) missing/empty/invalid: code/data/entropy_detector.py
