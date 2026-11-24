# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001d** — The evidence shows a `data/results/` directory with files, but it exists inside the project subdirectory (`projects/PROJ-723‑.../data/results/`), not at the repository’s top‑level as the task requires. A top‑level `data/results/` directory is missing.
- **T002** — The provided `requirements.txt` exists and contains the required pinned packages (plus extra ones), but there is no evidence (e.g., install logs or command output) showing that `pip install -r requirements.txt` actually succeeded in a clean environment. The verification step is missing.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
