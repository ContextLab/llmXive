# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000** — The provided `requirements.txt` is at the project root (not in `code/`) and omits the required `ucimlrepo` package; the `pyproject.toml` lists version ranges (`>=`) instead of exact pins. A correctly placed, fully pinned requirements file (or pyproject with exact versions) including all specified dependencies is missing.
- **T001** — Requested task execution failed; rerun successfully: code/data/fetch_real.py exit=1
