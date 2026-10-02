# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002a** — No `.flake8` configuration file was presented or referenced in the provided evidence, so the required artifact is missing. The implementer must add a non‑empty `.flake8` file with appropriate linting settings to satisfy task T002a.
- **T002b** — No `.pylintrc` configuration file was presented in the evidence; the required artifact is missing, so the task of creating a linting configuration has not been satisfied.
- **T004a** — No evidence of the required `data/raw/`, `data/processed/`, or `output/` directories is provided; the claim is unsubstantiated and the artifacts are missing.
- **T015b** — The provided `code/mask.py` does not contain the required secondary verification step that compares T015 output to analytical expectations, nor does it write any results to `data/processed/mask_verification.log` (the log file is missing). The buffer‑zone function is present but does not enforce a 2‑pixel buffer nor perform the mandated verification and logging.
- **T018** — declared artifact(s) missing/empty/invalid: data/processed/masked_cmb_n128.fits
- **T016a** — declared artifact(s) missing/empty/invalid: data/processed/masked_cmb_n128.fits, data/processed/coverage_report.json
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/masked_cmb_n128.fits, data/processed/map_stats.json
