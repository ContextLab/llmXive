# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The provided `code/requirements.txt` lists minimum version constraints (e.g., `torch>=2.2.0`) instead of exact, pinned versions, and `code/config.py` does not contain any logic that enforces a 6.3 GB memory limit (only sets `device` to CPU). Both the pinned‑dependency and memory‑limit requirements are therefore unmet.
