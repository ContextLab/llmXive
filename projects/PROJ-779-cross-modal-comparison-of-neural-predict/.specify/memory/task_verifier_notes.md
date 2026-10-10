# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The provided `requirements.txt` exists but does not meet the task: it uses open-ended `>=` version specifiers instead of exact pinned versions, includes extra unrelated packages, and lists `h5py` rather than the required `hpy`. The file therefore fails to satisfy the specification.
- **T003** — The evidence only includes a `requirements.txt` file; there is no `.venv` directory, no record of a virtual environment being created, and no `pip list` output showing that the listed packages (with the required versions) are installed. These required artifacts are missing, so the task is not satisfied.
- **T004** — The provided `.ruff.toml` is empty and does not contain a `[tool.ruff]` configuration section as required, and there is no execution evidence showing that `ruff check code/` and `black --check code/` were run successfully without errors.
- **T015** — declared artifact(s) missing/empty/invalid: code/data/download_auditory.py
- **T016** — declared artifact(s) missing/empty/invalid: code/data/download_visual.py
- **T016a** — declared artifact(s) missing/empty/invalid: code/data/checksums.py, state/projects/PROJ-779-cross-modal-comparison-of-neural-predict.yaml, state/...yaml
- **T017** — declared artifact(s) missing/empty/invalid: code/data/download_auditory.py
- **T018** — declared artifact(s) missing/empty/invalid: code/data/download_visual.py
- **T040** — declared artifact(s) missing/empty/invalid: code/analysis/stats_permutation.py
- **T041** — declared artifact(s) missing/empty/invalid: code/analysis/stats_ttest.py
- **T042** — declared artifact(s) missing/empty/invalid: code/analysis/stats_tost.py
- **T043** — declared artifact(s) missing/empty/invalid: code/analysis/stats_bh.py
- **T043b** — declared artifact(s) missing/empty/invalid: code/analysis/stats_bh.py, data/results/bh_corrected_pvalues.json
- **T049** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
- **T057** — declared artifact(s) missing/empty/invalid: data/results/final_report.md
- **T059** — declared artifact(s) missing/empty/invalid: docs/deviation-sc-002.md
