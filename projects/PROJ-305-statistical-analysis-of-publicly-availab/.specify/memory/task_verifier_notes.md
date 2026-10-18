# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The collector evidence shows several required directories do not exist: `src/validation/`, `tests/fixtures/`, `data/processed/`, `data/results/`, and `output/figures/` are all MISSING. While `logs/structure.txt` is non-empty (4567 bytes) and `quickstart.md` documents `python -m src.main`, the structure log itself confirms these directories were never created (it lists only `src/analysis`, `src/data`, `src/utils`, `data/raw`, `output/temporal_profiles`, etc.), so the directory-creation requirement and its verification (grep count of listed directories) cannot succeed. The implementer must creat
- **T002** — Requested task execution failed; rerun successfully: src/data/download.py exit=1
