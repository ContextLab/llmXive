# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The directory hierarchy and `specs/001-quantifying-correlations-between-solar-w/quickstart.md` (containing the required `python -m code.main --stage all` command) are present. However, there is no evidence that `code/main.py` (or `code/__init__.py`) exists — the collector only confirmed the `code/data/`, `code/analysis/`, `code/viz/`, and `code/tests/` subdirectories — so the required runnable entry point for `python -m code.main --help` is missing, and no execution evidence shows the verification command exits 0. Add `code/main.py` with a `--stage`/`--help` CLI (plus `code/__init__.py`) and d
- **T002** — Requested task execution failed; rerun successfully: code/data/fetch_ace.py exit=2; code/data/fetch_noaa.py exit=2
- **T003** — Requested task execution failed; rerun successfully: code/data/sync.py exit=1
