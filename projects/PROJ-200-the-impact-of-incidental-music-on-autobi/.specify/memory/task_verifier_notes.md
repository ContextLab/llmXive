# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The directories, `requirements.txt` (statsmodels, pyarrow, python-levenshtein), and `quickstart.md` with execution commands all exist, but `code/config.py` does not contain the required thresholds — there is no Levenshtein ≤ 4 threshold and no `MATCH_RATE_THRESHOLD=0.8`; it only exposes a random seed and dataset settings. The implementer must add these threshold constants (e.g., `LEVENSHTEIN_THRESHOLD = 4`, `MATCH_RATE_THRESHOLD = 0.8`) to `code/config.py`.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
- **T004** — Requested task execution failed; rerun successfully: code/data_ingestion.py exit=1
